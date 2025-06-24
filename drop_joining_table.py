#!/usr/bin/env python3
"""
Drop Joining Table Migration Script

This script removes the joining table from the database after successful migration
to ItemMaster. All joining table functionality has been moved to ItemMaster.

IMPORTANT: Make sure you have a backup before running this script!
"""

import os
from dotenv import load_dotenv
from flask import Flask
from database import db
from sqlalchemy import text

def drop_joining_table():
    """Drop the joining table and related constraints."""
    
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
            print("🔍 Checking if joining table exists...")
            
            # Check if joining table exists
            result = db.session.execute(text("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'joining'
            """))
            
            table_exists = result.fetchone()
            
            if not table_exists:
                print("ℹ️  Joining table does not exist. Nothing to drop.")
                return True
            
            # Check if joining_allergen table exists (depends on joining table)
            print("🔍 Checking for joining_allergen dependency table...")
            result = db.session.execute(text("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'joining_allergen'
            """))
            
            joining_allergen_exists = result.fetchone()
            
            if joining_allergen_exists:
                print("🗑️  Dropping joining_allergen table (dependency)...")
                db.session.execute(text("DROP TABLE joining_allergen"))
                print("✅ Successfully dropped joining_allergen table")
            
            # Drop the joining table
            print("🗑️  Dropping joining table...")
            db.session.execute(text("DROP TABLE joining"))
            
            # Commit the changes
            db.session.commit()
            print("✅ Successfully dropped joining table")
            
            # Verify tables were dropped
            print("\n🔍 Verifying tables were dropped...")
            result = db.session.execute(text("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME IN ('joining', 'joining_allergen')
            """))
            
            remaining_tables = result.fetchall()
            
            if remaining_tables:
                print("⚠️  Warning: Some tables still exist:")
                for table in remaining_tables:
                    print(f"  - {table[0]}")
                return False
            else:
                print("✅ All joining-related tables successfully removed")
                return True
            
        except Exception as e:
            print(f"❌ Error dropping joining table: {str(e)}")
            db.session.rollback()
            return False

def show_warning():
    """Show warning message before proceeding."""
    print("⚠️  WARNING: This script will permanently drop the joining table!")
    print("📋 Migration Summary:")
    print("   - joining table → ItemMaster table")
    print("   - All data has been migrated to ItemMaster")
    print("   - All controllers updated to use ItemMaster")
    print("   - joining_allergen table will also be dropped")
    print()
    print("🔒 BACKUP RECOMMENDATION:")
    print("   Make sure you have a database backup before proceeding!")
    print()
    
    response = input("Do you want to proceed? (yes/no): ").strip().lower()
    return response in ['yes', 'y']

if __name__ == "__main__":
    print("🚀 Joining Table Removal Script")
    print("=" * 50)
    
    if show_warning():
        print("\n🏃‍♂️ Proceeding with joining table removal...")
        
        if drop_joining_table():
            print("\n🎉 Joining table removal completed successfully!")
            print("📝 Summary:")
            print("   ✅ joining table dropped")
            print("   ✅ joining_allergen table dropped")
            print("   ✅ All functionality preserved in ItemMaster")
            print("\n🔄 Next Steps:")
            print("   1. Test application functionality")
            print("   2. Verify all features work with ItemMaster")
            print("   3. Remove any remaining joining references if found")
        else:
            print("\n❌ Joining table removal failed!")
            print("📝 Please check the error messages above and try again.")
    else:
        print("\n🛑 Operation cancelled by user.")
        print("💡 Run this script again when you're ready to proceed.") 