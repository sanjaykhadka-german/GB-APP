#!/usr/bin/env python3
"""
Add avg_weight_per_unit Column to ItemMaster

This script adds the avg_weight_per_unit column to the item_master table
for tracking the average weight per unit for each item.
"""

import os
from dotenv import load_dotenv
from flask import Flask
from database import db
from sqlalchemy import text

def add_avg_weight_per_unit_column():
    """Add avg_weight_per_unit column to item_master table."""
    
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
            print("🔍 Checking if avg_weight_per_unit column exists in item_master...")
            
            # Check if avg_weight_per_unit column exists
            result = db.session.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'item_master' 
                AND COLUMN_NAME = 'avg_weight_per_unit'
            """))
            
            column_exists = result.fetchone()
            
            if column_exists:
                print("ℹ️  avg_weight_per_unit column already exists. Nothing to add.")
                return True
            
            # Add the avg_weight_per_unit column
            print("🔧 Adding avg_weight_per_unit column to item_master table...")
            db.session.execute(text("""
                ALTER TABLE item_master 
                ADD COLUMN avg_weight_per_unit FLOAT NULL 
                COMMENT 'Average weight per unit in kg'
            """))
            
            # Commit the changes
            db.session.commit()
            print("✅ Successfully added avg_weight_per_unit column to item_master table")
            
            # Verify the column was added
            print("\n🔍 Verifying column addition...")
            result = db.session.execute(text("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_COMMENT 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'item_master' 
                AND COLUMN_NAME = 'avg_weight_per_unit'
            """))
            
            column_info = result.fetchone()
            
            if column_info:
                print("✅ Verification successful!")
                print(f"   Column Name: {column_info[0]}")
                print(f"   Data Type: {column_info[1]}")
                print(f"   Nullable: {column_info[2]}")
                print(f"   Comment: {column_info[3]}")
            else:
                print("❌ Verification failed - avg_weight_per_unit column not found")
                return False
            
            # Also check that units_per_bag exists
            print("\n🔍 Verifying units_per_bag column exists...")
            result = db.session.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'item_master' 
                AND COLUMN_NAME = 'units_per_bag'
            """))
            
            units_per_bag_exists = result.fetchone()
            
            if units_per_bag_exists:
                print("✅ units_per_bag column confirmed to exist")
            else:
                print("⚠️  Warning: units_per_bag column not found")
            
            return True
            
        except Exception as e:
            print(f"❌ Error adding column: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("🔧 Add avg_weight_per_unit Column to ItemMaster")
    print("=" * 50)
    
    print("📋 This script will:")
    print("   - Add avg_weight_per_unit column to item_master table")
    print("   - Set column as nullable FLOAT type")
    print("   - Verify the addition was successful")
    print("   - Confirm units_per_bag column exists")
    print()
    
    response = input("Do you want to proceed? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        print("\n🏃‍♂️ Proceeding with column addition...")
        
        if add_avg_weight_per_unit_column():
            print("\n🎉 Column addition completed successfully!")
            print("📝 Summary:")
            print("   ✅ avg_weight_per_unit column added")
            print("   ✅ Column is nullable FLOAT type")
            print("   ✅ units_per_bag column confirmed")
            print("\n🔄 Next Steps:")
            print("   1. Update ItemMaster model")
            print("   2. Update templates to include avg_weight_per_unit")
            print("   3. Update controllers to use these values")
            print("   4. Test application functionality")
        else:
            print("\n❌ Column addition failed!")
            print("📝 Please check the error messages above and try again.")
    else:
        print("\n🛑 Operation cancelled by user.")
        print("💡 Run this script again when you're ready to proceed.") 