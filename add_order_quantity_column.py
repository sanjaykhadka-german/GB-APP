#!/usr/bin/env python3
"""
Add order_quantity column to raw_material_stocktake table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from database import db
from app import app

def add_order_quantity_column():
    """Add order_quantity column to raw_material_stocktake table"""
    try:
        with app.app_context():
            # Check if column already exists
            result = db.session.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = 'raw_material_stocktake' 
                AND column_name = 'order_quantity'
            """))
            
            if result.scalar() > 0:
                print("Column 'order_quantity' already exists in raw_material_stocktake table")
                return True
            
            # Add the column
            db.session.execute(text("""
                ALTER TABLE raw_material_stocktake 
                ADD COLUMN order_quantity FLOAT NOT NULL DEFAULT 0.0 
                AFTER current_stock
            """))
            
            # Commit the changes
            db.session.commit()
            print("Successfully added 'order_quantity' column to raw_material_stocktake table")
            return True
            
    except Exception as e:
        print(f"Error adding order_quantity column: {str(e)}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    print("Starting migration to add order_quantity column...")
    
    success = add_order_quantity_column()
    
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")
        sys.exit(1) 