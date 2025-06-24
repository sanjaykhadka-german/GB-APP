#!/usr/bin/env python3

# ========================================
# DEPRECATED: Joining table has been removed
# All functionality migrated to ItemMaster
# This script is kept for historical reference only
# ========================================

"""
import os
from dotenv import load_dotenv
from flask import Flask
from database import db
from models.joining import Joining
from sqlalchemy import text

def add_weekly_average_to_joining():
    # Load environment variables
    load_dotenv()
    
    # Create Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    with app.app_context():
        try:
            # Check if the column already exists
            print("Checking if weekly_average column exists...")
            result = db.session.execute(text(\"\"\"
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'joining' 
                AND COLUMN_NAME = 'weekly_average'
            \"\"\"))
            
            column_exists = result.fetchone()
            
            if column_exists:
                print("✅ weekly_average column already exists in joining table")
                return True
            
            # Add the weekly_average column
            print("Adding weekly_average column to joining table...")
            db.session.execute(text(\"\"\"
                ALTER TABLE joining 
                ADD COLUMN weekly_average FLOAT NULL
            \"\"\"))
            
            # Commit the changes
            db.session.commit()
            print("✅ Successfully added weekly_average column to joining table")
            
            # Verify the column was added
            print("\\nVerifying table structure...")
            result = db.session.execute(text("DESCRIBE joining"))
            columns = result.fetchall()
            
            print("Updated joining table structure:")
            for column in columns:
                print(f"  {column[0]} | {column[1]} | Null: {column[2]} | Key: {column[3]} | Default: {column[4]}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    if add_weekly_average_to_joining():
        print("\\n🎉 Weekly average column addition completed successfully!")
    else:
        print("\\n💥 Weekly average column addition failed!")
"""

print("DEPRECATED: This script is no longer needed. Joining table has been migrated to ItemMaster.") 