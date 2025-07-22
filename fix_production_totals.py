#!/usr/bin/env python3
"""
Fix Production Totals Script
===========================

This script fixes production totals by:
1. Ensuring production totals match packing requirements
2. Correcting batch calculations (total_kg / 300)
3. Removing any double-counting of filling totals
"""

import sys
import os
from datetime import datetime
import logging

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from database import db
from models.packing import Packing
from models.production import Production
from models.filling import Filling
from models.item_master import ItemMaster
from sqlalchemy import func
from controllers.bom_service import BOMService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_production_totals():
    """Fix production totals and batch calculations."""
    try:
        # Get all unique dates that have packing entries
        dates = db.session.query(
            Packing.packing_date,
            Packing.week_commencing
        ).distinct().all()
        
        logger.info(f"Found {len(dates)} dates to process")
        
        # Process each date
        for date, week in dates:
            logger.info(f"\nProcessing {date}, week {week}")
            
            # Get packing total for this date
            packing_total = db.session.query(
                func.sum(Packing.requirement_kg)
            ).filter(
                Packing.packing_date == date,
                Packing.week_commencing == week
            ).scalar() or 0.0
            
            logger.info(f"Packing total for {date}: {packing_total:.1f} kg")
            
            # Recalculate production requirements
            success, message = BOMService.update_downstream_requirements(week)
            if not success:
                logger.error(f"Failed to update requirements for {date}: {message}")
                continue
                
            # Verify the fix
            production_total = db.session.query(
                func.sum(Production.total_kg)
            ).filter(
                Production.production_date == date,
                Production.week_commencing == week
            ).scalar() or 0.0
            
            logger.info(f"New production total: {production_total:.1f} kg")
            
            if abs(production_total - packing_total) < 0.1:
                logger.info("✅ Production total now matches packing total!")
            else:
                logger.error(f"❌ Still mismatched! Difference: {production_total - packing_total:.1f} kg")
        
        # Final verification
        total_packing = db.session.query(
            func.sum(Packing.requirement_kg)
        ).scalar() or 0.0
        
        total_production = db.session.query(
            func.sum(Production.total_kg)
        ).scalar() or 0.0
        
        logger.info("\nFinal Totals:")
        logger.info(f"Total Packing: {total_packing:.1f} kg")
        logger.info(f"Total Production: {total_production:.1f} kg")
        
        if abs(total_production - total_packing) < 0.1:
            logger.info("✅ Overall totals match!")
        else:
            logger.error(f"❌ Overall totals still mismatched! Difference: {total_production - total_packing:.1f} kg")
        
    except Exception as e:
        logger.error(f"Error fixing production totals: {str(e)}")
        db.session.rollback()
        raise e

if __name__ == '__main__':
    with app.app_context():
        fix_production_totals() 