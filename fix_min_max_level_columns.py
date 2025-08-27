#!/usr/bin/env python3
"""
Migration script to change min_level and max_level columns from DECIMAL to INTEGER
This will fix the issue with 4 decimal places being displayed.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import Flask app and create context
from app import app
from database import db
from models.packing import Packing
from sqlalchemy import text
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_min_max_level_columns():
    """Migrate min_level and max_level columns from DECIMAL to INTEGER"""
    try:
        logger.info("Starting migration of min_level and max_level columns...")
        
        # Get database connection
        engine = db.engine
        
        # Tables to migrate
        tables_to_migrate = [
            ('packing', ['min_level', 'max_level']),
            ('item_master', ['min_level', 'max_level'])
        ]
        
        for table_name, columns in tables_to_migrate:
            logger.info(f"Processing table: {table_name}")
            
            # Check current column types
            with engine.connect() as conn:
                # Get table information
                result = conn.execute(text(f"""
                    SELECT COLUMN_NAME, DATA_TYPE, NUMERIC_PRECISION, NUMERIC_SCALE
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = '{table_name}' 
                    AND COLUMN_NAME IN ({', '.join([f"'{col}'" for col in columns])})
                """))
                
                table_columns = result.fetchall()
                logger.info(f"Current column definitions for {table_name}: {table_columns}")
                
                # Check if columns are already INTEGER
                for col in table_columns:
                    if col[1] == 'int':
                        logger.info(f"Column {col[0]} in {table_name} is already INTEGER type")
                        continue
                        
                    logger.info(f"Converting column {col[0]} in {table_name} from {col[1]} to INTEGER")
                    
                    # Convert DECIMAL to INTEGER
                    # First, update any NULL values to 0
                    conn.execute(text(f"UPDATE {table_name} SET {col[0]} = 0 WHERE {col[0]} IS NULL"))
                    
                    # Convert the column type
                    conn.execute(text(f"ALTER TABLE {table_name} MODIFY COLUMN {col[0]} INT"))
                    
                    logger.info(f"Successfully converted {col[0]} in {table_name} to INTEGER")
                
                # Commit the changes for this table
                conn.commit()
                logger.info(f"Completed migration for table {table_name}")
        
        logger.info("All migrations completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise

def verify_migration():
    """Verify that the migration was successful"""
    try:
        logger.info("Verifying migration...")
        
        # Tables to verify
        tables_to_verify = [
            ('packing', ['min_level', 'max_level']),
            ('item_master', ['min_level', 'max_level'])
        ]
        
        # Check column types again
        engine = db.engine
        with engine.connect() as conn:
            for table_name, columns in tables_to_verify:
                logger.info(f"Verifying table: {table_name}")
                
                result = conn.execute(text(f"""
                    SELECT COLUMN_NAME, DATA_TYPE, NUMERIC_PRECISION, NUMERIC_SCALE
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = '{table_name}' 
                    AND COLUMN_NAME IN ({', '.join([f"'{col}'" for col in columns])})
                """))
                
                table_columns = result.fetchall()
                logger.info(f"Post-migration column definitions for {table_name}: {table_columns}")
                
                # Verify all columns are now INTEGER
                for col in table_columns:
                    if col[1] != 'int':
                        logger.error(f"Column {col[0]} in {table_name} is still {col[1]} type!")
                        return False
                    else:
                        logger.info(f"Column {col[0]} in {table_name} is correctly INTEGER type")
        
        logger.info("Migration verification successful!")
        return True
        
    except Exception as e:
        logger.error(f"Verification failed: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        logger.info("Starting min_level/max_level column migration...")
        
        # Run the migration within Flask app context
        with app.app_context():
            # Run the migration
            migrate_min_max_level_columns()
            
            # Verify the migration
            if verify_migration():
                logger.info("✅ Migration completed and verified successfully!")
            else:
                logger.error("❌ Migration verification failed!")
                sys.exit(1)
                
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        sys.exit(1)
