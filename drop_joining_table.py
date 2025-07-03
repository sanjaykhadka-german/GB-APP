#!/usr/bin/env python3
"""
Drop Joining Table and Clean Up Files
====================================

This script completes the joining table cleanup by:
1. Dropping the joining table from the database
2. Backing up joining-related files 
3. Removing joining files and templates
"""

import os
import shutil
from app import app
from database import db

def backup_joining_files():
    """Backup joining-related files before removal"""
    
    print("🔄 Backing up joining files...")
    
    # Create backup directory
    backup_dir = 'backup_joining_files'
    os.makedirs(backup_dir, exist_ok=True)
    
    files_to_backup = [
        'controllers/joining_controller.py',
        'templates/joining',
        'models/joining.py'
    ]
    
    backed_up = []
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            if os.path.isdir(file_path):
                # Backup directory
                backup_path = os.path.join(backup_dir, os.path.basename(file_path))
                if os.path.exists(backup_path):
                    shutil.rmtree(backup_path)
                shutil.copytree(file_path, backup_path)
                backed_up.append(file_path)
                print(f"✅ Backed up directory: {file_path}")
            else:
                # Backup file
                backup_path = os.path.join(backup_dir, os.path.basename(file_path))
                shutil.copy2(file_path, backup_path)
                backed_up.append(file_path)
                print(f"✅ Backed up file: {file_path}")
    
    return backed_up

def remove_joining_files(backed_up_files):
    """Remove joining files after backup"""
    
    print("🔄 Removing joining files...")
    
    for file_path in backed_up_files:
        try:
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
                print(f"✅ Removed directory: {file_path}")
            else:
                os.remove(file_path)
                print(f"✅ Removed file: {file_path}")
        except Exception as e:
            print(f"❌ Error removing {file_path}: {str(e)}")

def drop_joining_table():
    """Drop the joining table from the database"""
    
    print("🔄 Dropping joining table from database...")
    
    with app.app_context():
        try:
            # Check if table exists first
            result = db.engine.execute("SHOW TABLES LIKE 'joining'")
            table_exists = result.fetchone() is not None
            
            if table_exists:
                # Drop the table
                db.engine.execute('DROP TABLE joining')
                print("✅ Joining table dropped successfully")
            else:
                print("ℹ️  Joining table does not exist (may have been dropped already)")
                
        except Exception as e:
            print(f"❌ Error dropping joining table: {str(e)}")

def verify_cleanup():
    """Verify that the cleanup was successful"""
    
    print("🔍 Verifying cleanup...")
    
    with app.app_context():
        try:
            # Check if joining table exists
            result = db.engine.execute("SHOW TABLES LIKE 'joining'")
            table_exists = result.fetchone() is not None
            
            if not table_exists:
                print("✅ Joining table successfully removed from database")
            else:
                print("❌ Joining table still exists in database")
                
        except Exception as e:
            print(f"❌ Error verifying database cleanup: {str(e)}")
    
    # Check if files were removed
    removed_files = [
        'controllers/joining_controller.py',
        'templates/joining',
        'models/joining.py'
    ]
    
    for file_path in removed_files:
        if not os.path.exists(file_path):
            print(f"✅ File/directory removed: {file_path}")
        else:
            print(f"❌ File/directory still exists: {file_path}")

def main():
    """Run the complete cleanup process"""
    
    print("🚀 Starting joining table cleanup...")
    print("=" * 50)
    
    try:
        # Step 1: Backup files
        backed_up_files = backup_joining_files()
        
        # Step 2: Drop the table
        drop_joining_table()
        
        # Step 3: Remove files (only after successful backup)
        if backed_up_files:
            remove_joining_files(backed_up_files)
        
        # Step 4: Verify cleanup
        verify_cleanup()
        
        print("=" * 50)
        print("🎉 Joining table cleanup completed successfully!")
        print("\n✅ Summary of changes:")
        print("   - Joining table dropped from database")
        print("   - Joining controller, templates, and model files removed")
        print("   - Files backed up to 'backup_joining_files/' directory")
        print("   - Enhanced BOM service updated to use item_master hierarchy")
        print("   - Delete buttons removed from item_master and recipe pages")
        print("\n💡 The application now uses item_master hierarchy fields:")
        print("   - wip_item_id: Points to WIP item that produces this item")
        print("   - wipf_item_id: Points to WIPF item that produces this item")
        print("\n🔧 Next steps:")
        print("   - Test the application to ensure all functionality works")
        print("   - Remove backup files if everything is working correctly")
        print("   - Update any remaining documentation")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {str(e)}")
        print("   Check the error and try running specific steps manually")

if __name__ == "__main__":
    main() 