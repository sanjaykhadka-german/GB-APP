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
            # Get all unique dates that have production entries
            production_dates = db.session.query(
                Production.production_date,
                Production.week_commencing
            ).distinct().all()
            
            for prod_date, week_comm in production_dates:
                logger.info(f"\nProcessing date: {prod_date}, week: {week_comm}")
                
                # Get all packing requirements for this date/week, grouped by recipe family
                packing_reqs = db.session.query(
                    func.substring_index(ItemMaster.item_code, '.', 1).label('recipe_family'),
                    func.sum(Packing.requirement_kg).label('total_kg')
                ).join(
                    ItemMaster, Packing.item_id == ItemMaster.id
                ).filter(
                    Packing.packing_date == prod_date,
                    Packing.week_commencing == week_comm
                ).group_by(
                    func.substring_index(ItemMaster.item_code, '.', 1)
                ).all()
                
                # Delete existing production entries for this date/week
                Production.query.filter_by(
                    production_date=prod_date,
                    week_commencing=week_comm
                ).delete()
                
                # Create new production entries based on grouped packing requirements
                for recipe_family, total_kg in packing_reqs:
                    if not total_kg:
                        continue
                        
                    # Get the WIP item for this recipe family
                    wip_item = ItemMaster.query.join(ItemMaster.item_type).filter(
                        ItemMaster.item_code == recipe_family,
                        ItemMaster.item_type.has(type_name='WIP')
                    ).first()
                    
                    if not wip_item:
                        logger.warning(f"No WIP item found for recipe family {recipe_family}")
                        continue
                    
                    # Calculate batches
                    batches = total_kg / 300.0 if total_kg > 0 else 0.0
                    
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
            logger.info("\nProduction-packing synchronization completed successfully!")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error fixing production-packing sync: {str(e)}")
            raise

if __name__ == '__main__':
    fix_production_packing_sync() 