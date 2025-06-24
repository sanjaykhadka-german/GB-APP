#!/usr/bin/env python3
"""
Add category_id column to raw_material_stocktake table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from database import db
from app import app

def add_category_id_column():
    """Add category_id column to raw_material_stocktake table"""
    try:
        with app.app_context():
            # Check if column already exists
            result = db.session.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = 'raw_material_stocktake' 
                AND column_name = 'category_id'
            """))
            
            if result.scalar() > 0:
                print("Column 'category_id' already exists in raw_material_stocktake table")
                return True
            
            # Add the column
            db.session.execute(text("""
                ALTER TABLE raw_material_stocktake 
                ADD COLUMN category_id INT NULL 
                AFTER item_code,
                ADD CONSTRAINT fk_stocktake_category 
                FOREIGN KEY (category_id) REFERENCES category(id)
            """))
            
            # Commit the changes
            db.session.commit()
            print("Successfully added 'category_id' column to raw_material_stocktake table")
            return True
            
    except Exception as e:
        print(f"Error adding category_id column: {str(e)}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    print("Starting migration to add category_id column...")
    
    success = add_category_id_column()
    
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")
        sys.exit(1) 