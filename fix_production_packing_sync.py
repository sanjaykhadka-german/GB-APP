#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models.packing import Packing
from models.production import Production
from models.item_master import ItemMaster
from models.item_type import ItemType
from sqlalchemy import func
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_production_packing_sync():
    with app.app_context():
        try:
            # Get all unique dates that have packing entries
            packing_dates = db.session.query(
                Packing.packing_date,
                Packing.week_commencing
            ).distinct().all()
            
            for pack_date, week_comm in packing_dates:
                logger.info(f"\nProcessing date: {pack_date}, week: {week_comm}")
                
                # Get all packing entries for this date
                packings = Packing.query.join(ItemMaster).filter(
                    Packing.packing_date == pack_date,
                    Packing.week_commencing == week_comm
                ).all()
                
                # Group by recipe family
                recipe_family_totals = {}
                for packing in packings:
                    if not packing.item:
                        logger.warning(f"Packing {packing.id} has no associated item")
                        continue
                        
                    # Get recipe family from item code
                    recipe_family = packing.item.item_code.split('.')[0]
                    
                    # Initialize recipe family data if not exists
                    if recipe_family not in recipe_family_totals:
                        recipe_family_totals[recipe_family] = {
                            'total_kg': 0.0,
                            'items': [],
                            'wip_item': None
                        }
                        
                        # Find WIP item for this recipe family
                        wip_item = ItemMaster.query.join(ItemMaster.item_type).filter(
                            ItemMaster.item_code == recipe_family,
                            ItemMaster.item_type.has(type_name='WIP')
                        ).first()
                        
                        if not wip_item:
                            logger.warning(f"No WIP item found for recipe family {recipe_family}")
                            continue
                            
                        recipe_family_totals[recipe_family]['wip_item'] = wip_item
                    
                    # Add packing requirement to total
                    requirement_kg = packing.requirement_kg or 0.0
                    recipe_family_totals[recipe_family]['total_kg'] += requirement_kg
                    recipe_family_totals[recipe_family]['items'].append(
                        f"{packing.item.item_code}: {requirement_kg:.1f} kg"
                    )
                
                # Delete existing production entries for this date/week
                Production.query.filter(
                    Production.production_date == pack_date,
                    Production.week_commencing == week_comm
                ).delete()
                
                # Create new production entries based ONLY on packing requirements
                for recipe_family, data in recipe_family_totals.items():
                    if not data['wip_item']:
                        continue
                        
                    total_kg = data['total_kg']
                    if total_kg <= 0:
                        logger.info(f"Skipping {recipe_family} - no production required")
                        continue
                    
                    # Calculate batches (300kg per batch)
                    batches = total_kg / 300.0
                    
                    # Create production entry
                    new_production = Production(
                        production_date=pack_date,
                        week_commencing=week_comm,
                        item_id=data['wip_item'].id,
                        production_code=recipe_family,
                        description=data['wip_item'].description,
                        total_kg=total_kg,
                        batches=batches
                    )
                    db.session.add(new_production)
                    
                    logger.info(f"Created production entry for {recipe_family}:")
                    logger.info(f"  Total: {total_kg:.1f} kg ({batches:.2f} batches)")
                    logger.info(f"  From items:")
                    for item in data['items']:
                        logger.info(f"    - {item}")
            
            db.session.commit()
            logger.info("\nProduction-packing synchronization completed successfully!")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error fixing production-packing sync: {str(e)}")
            raise

if __name__ == '__main__':
    fix_production_packing_sync() 