#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models.packing import Packing
from models.production import Production
from models.item_master import ItemMaster
from sqlalchemy import func
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_data_integrity():
    with app.app_context():
        try:
            # 1. Check for orphaned records
            logger.info("\nChecking for orphaned records...")
            
            # Check packing records
            orphaned_packing = Packing.query.filter(
                ~Packing.item_id.in_(db.session.query(ItemMaster.id))
            ).all()
            if orphaned_packing:
                logger.error(f"Found {len(orphaned_packing)} packing records with invalid item_id")
                for p in orphaned_packing:
                    logger.error(f"Packing ID: {p.id}, Item ID: {p.item_id}")
            
            # Check production records
            orphaned_production = Production.query.filter(
                ~Production.item_id.in_(db.session.query(ItemMaster.id))
            ).all()
            if orphaned_production:
                logger.error(f"Found {len(orphaned_production)} production records with invalid item_id")
                for p in orphaned_production:
                    logger.error(f"Production ID: {p.id}, Item ID: {p.item_id}")
            
            # 2. Check for mismatched totals
            logger.info("\nChecking for mismatched totals...")
            
            dates = db.session.query(
                Packing.packing_date,
                Packing.week_commencing
            ).distinct().all()
            
            for date, week in dates:
                # Get all packing entries for this date
                packings = Packing.query.join(ItemMaster).filter(
                    Packing.packing_date == date,
                    Packing.week_commencing == week
                ).all()
                
                # Group by recipe family
                recipe_family_totals = {}
                for packing in packings:
                    if not packing.item:
                        continue
                    recipe_family = packing.item.item_code.split('.')[0]
                    if recipe_family not in recipe_family_totals:
                        recipe_family_totals[recipe_family] = {
                            'total_kg': 0.0,
                            'items': []
                        }
                    recipe_family_totals[recipe_family]['total_kg'] += packing.requirement_kg or 0.0
                    recipe_family_totals[recipe_family]['items'].append(packing.item.item_code)
                
                # Compare with production entries
                for recipe_family, data in recipe_family_totals.items():
                    production = Production.query.filter(
                        Production.production_code == recipe_family,
                        Production.production_date == date,
                        Production.week_commencing == week
                    ).first()
                    
                    if not production:
                        logger.error(f"\nMissing production entry for recipe family {recipe_family}")
                        logger.error(f"Date: {date}, Week: {week}")
                        logger.error(f"Packing total: {data['total_kg']}")
                        logger.error(f"Items: {', '.join(data['items'])}")
                        continue
                    
                    if abs(data['total_kg'] - production.total_kg) >= 0.1:
                        logger.error(f"\nMismatch found for recipe family {recipe_family}")
                        logger.error(f"Date: {date}, Week: {week}")
                        logger.error(f"Packing total: {data['total_kg']}")
                        logger.error(f"Production total: {production.total_kg}")
                        logger.error(f"Difference: {data['total_kg'] - production.total_kg}")
                        logger.error(f"Items: {', '.join(data['items'])}")
            
            logger.info("\nData integrity check completed!")
            
        except Exception as e:
            logger.error(f"Error during verification: {str(e)}")
            raise

if __name__ == '__main__':
    verify_data_integrity() 