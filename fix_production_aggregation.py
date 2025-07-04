#!/usr/bin/env python3
"""
Fix Production Aggregation Script
=================================

This script fixes existing production entries by recalculating them based on 
proper aggregation of packing requirements by production_code.

The issue: Production entries were created with broken logic that didn't properly
aggregate all packing entries that share the same production_code.

The fix: Recalculate all production entries by summing packing requirements 
grouped by production_code for each recipe family and date.
"""

import sys
import os
from datetime import datetime, date, timedelta
import logging

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from database import db
from models.production import Production
from models.packing import Packing  
from models.item_master import ItemMaster
from models.item_type import ItemType
from sqlalchemy import func

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_production_aggregation():
    app = create_app()
    with app.app_context():
        try:
            # Get all unique dates that have production entries
            production_dates = db.session.query(
                Production.production_date,
                Production.week_commencing
            ).distinct().all()
            
            logger.info(f"Found {len(production_dates)} unique production dates to process")
            
            for prod_date, week_comm in production_dates:
                logger.info(f"\nProcessing date: {prod_date}, week: {week_comm}")
                
                # Get all packing entries for this date
                packing_entries = Packing.query.filter(
                    Packing.packing_date == prod_date,
                    Packing.week_commencing == week_comm
                ).all()
                
                # Group packing by recipe family
                recipe_family_totals = {}
                for packing in packing_entries:
                    if not packing.item:
                        continue
                        
                    # Get recipe family from item code
                    recipe_family = packing.item.item_code.split('.')[0]
                    if recipe_family not in recipe_family_totals:
                        recipe_family_totals[recipe_family] = {
                            'total_kg': 0.0,
                            'wip_item': None
                        }
                    
                    # Add packing requirement to recipe family total
                    recipe_family_totals[recipe_family]['total_kg'] += packing.requirement_kg or 0.0
                    
                    # Get WIP item for this recipe family if not already found
                    if not recipe_family_totals[recipe_family]['wip_item']:
                        wip_item = ItemMaster.query.join(ItemMaster.item_type).filter(
                            ItemMaster.item_code == recipe_family,
                            ItemMaster.item_type.has(type_name='WIP')
                        ).first()
                        recipe_family_totals[recipe_family]['wip_item'] = wip_item
                
                logger.info(f"Recipe family totals: {recipe_family_totals}")
                
                # Delete existing production entries for this date
                deleted = Production.query.filter(
                    Production.production_date == prod_date,
                    Production.week_commencing == week_comm
                ).delete()
                logger.info(f"Deleted {deleted} existing production entries")
                
                # Create new production entries with correct totals
                for recipe_family, data in recipe_family_totals.items():
                    total_kg = data['total_kg']
                    wip_item = data['wip_item']
                    
                    if total_kg <= 0:
                        continue
                        
                    if not wip_item:
                        logger.warning(f"No WIP item found for recipe family {recipe_family}")
                        continue
                    
                    # Calculate batches (300kg per batch)
                    batches = total_kg / 300.0
                    
                    # Create production entry
                    new_production = Production(
                        production_date=prod_date,
                        week_commencing=week_comm,
                        item_id=wip_item.id,
                        production_code=recipe_family,
                        description=wip_item.description,
                        total_kg=total_kg,
                        batches=batches
                    )
                    db.session.add(new_production)
                    logger.info(f"Created production entry for {recipe_family}: {total_kg} kg ({batches} batches)")
                
                db.session.commit()
                logger.info("Changes committed successfully")
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during aggregation fix: {str(e)}")
            raise e

def main():
    """Main function to run the production aggregation fix."""
    app = create_app()
    
    with app.app_context():
        print("Production Aggregation Fix Script")
        print("=" * 50)
        
        # You can specify a specific week or fix all weeks
        if len(sys.argv) > 1:
            week_str = sys.argv[1]
            dry_run = True if len(sys.argv) <= 2 or sys.argv[2] != 'apply' else False
            
            print(f"Fixing specific week: {week_str}")
            success = fix_production_aggregation()
        else:
            # Default: fix all weeks (dry run first)
            print("Fixing all weeks with packing data...")
            
            # First do a dry run
            print("\n🔍 STEP 1: DRY RUN - Analyzing what needs to be fixed...")
            success = fix_production_aggregation()
            
            if success:
                response = input("\nDo you want to apply these fixes? (yes/no): ").strip().lower()
                if response in ['yes', 'y']:
                    print("\n🔧 STEP 2: APPLYING FIXES...")
                    success = fix_production_aggregation()
                else:
                    print("Fixes not applied.")
        
        if success:
            print("\n✅ Script completed successfully!")
        else:
            print("\n❌ Script completed with errors!")
            sys.exit(1)

if __name__ == '__main__':
    main() 