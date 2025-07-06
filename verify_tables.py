#!/usr/bin/env python3
"""
Verify Tables Script
===================

This script checks the state of tables before and after truncation.
"""

import sys
import os
import logging
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from database import db
from models.packing import Packing
from models.filling import Filling
from models.production import Production
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_table_counts():
    """Check row counts for each table."""
        try:
        # Check each table's count
        tables = {
            'packing': Packing,
            'filling': Filling,
            'production': Production
        }
        
        for table_name, model in tables.items():
            count = db.session.query(model).count()
            logger.info(f"{table_name}: {count} rows")
            
            # Get total kg for each table
            if table_name == 'packing':
                total = db.session.query(db.func.sum(Packing.requirement_kg)).scalar() or 0
                logger.info(f"{table_name} total kg: {total:.1f}")
            elif table_name == 'filling':
                total = db.session.query(db.func.sum(Filling.kilo_per_size)).scalar() or 0
                logger.info(f"{table_name} total kg: {total:.1f}")
            elif table_name == 'production':
                total = db.session.query(db.func.sum(Production.total_kg)).scalar() or 0
                logger.info(f"{table_name} total kg: {total:.1f}")
            
        return True
        
    except Exception as e:
        logger.error(f"Error checking tables: {str(e)}")
        return False

def truncate_tables():
    """Truncate all specified tables."""
    try:
        # Disable foreign key checks
        db.session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        
        # Truncate tables
        tables = [
            'packing',
            'filling',
            'production'
        ]
        
        for table in tables:
            db.session.execute(text(f"TRUNCATE TABLE {table}"))
            logger.info(f"Truncated {table}")
        
        # Re-enable foreign key checks
        db.session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        
        # Commit changes
        db.session.commit()
        return True

        except Exception as e:
        logger.error(f"Error truncating tables: {str(e)}")
        db.session.rollback()
        return False

def main():
    """Main function to verify table truncation."""
    app = create_app()
    with app.app_context():
        logger.info("\nChecking table counts before truncation:")
        check_table_counts()
        
        response = input("\nDo you want to proceed with truncating the tables? (yes/no): ").strip().lower()
        if response in ['yes', 'y']:
            logger.info("\nTruncating tables...")
            if truncate_tables():
                logger.info("\nChecking table counts after truncation:")
                check_table_counts()
                logger.info("\n✅ Tables truncated successfully!")
            else:
                logger.error("\n❌ Failed to truncate tables!")
        else:
            logger.info("Operation cancelled.")

if __name__ == '__main__':
    main() 