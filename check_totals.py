#!/usr/bin/env python3
"""
Check Totals Script
==================

This script checks the current packing and production totals.
"""

import sys
import os
from datetime import datetime
import logging

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from database import db
from models.packing import Packing
from models.production import Production
from models.filling import Filling
from sqlalchemy import func

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_totals():
    """Check current packing, production, and filling totals."""
    try:
        # Get packing total
        packing_total = db.session.query(
            func.sum(Packing.requirement_kg)
        ).scalar() or 0.0
        logger.info(f"\nPacking Total: {packing_total:.1f} kg")
        
        # Get production total
        production_total = db.session.query(
            func.sum(Production.total_kg)
        ).scalar() or 0.0
        logger.info(f"Production Total: {production_total:.1f} kg")
        
        # Get filling total
        filling_total = db.session.query(
            func.sum(Filling.kilo_per_size)
        ).scalar() or 0.0
        logger.info(f"Filling Total: {filling_total:.1f} kg")
        
        # Check if production total matches packing total
        if abs(production_total - packing_total) > 0.1:  # Allow small rounding differences
            logger.error("❌ Production total does not match packing total!")
            logger.error(f"Difference: {production_total - packing_total:.1f} kg")
        else:
            logger.info("✅ Production total matches packing total!")
            
        # Check if filling total is being added to production
        if production_total > packing_total + (filling_total * 0.5):  # If production is more than packing + half of filling
            logger.error("❌ Filling total appears to be added to production!")
            logger.error("Production should only come from packing requirements.")
        
        # Show production entries
        logger.info("\nProduction Entries:")
        production_entries = Production.query.all()
        for entry in production_entries:
            logger.info(f"- {entry.production_code}: {entry.total_kg:.1f} kg ({entry.batches:.2f} batches)")
            # Verify batch calculation
            expected_batches = entry.total_kg / 300
            if abs(expected_batches - entry.batches) > 0.01:  # Allow small rounding differences
                logger.error(f"  ❌ Incorrect batch calculation! Expected: {expected_batches:.2f}, Got: {entry.batches:.2f}")
        
    except Exception as e:
        logger.error(f"Error checking totals: {str(e)}")
        raise e

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        check_totals() 