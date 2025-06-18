#!/usr/bin/env python3
"""
Script to fix item types in ItemMaster table to match ItemType table
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from database import db
from models.item_master import ItemMaster

def fix_item_types():
    print("Fixing Item Types in ItemMaster table...")
    print("=" * 50)
    
    # Define the mapping from old to new values
    type_mapping = {
        'raw_material': 'Raw Material',
        'finished_good': 'Finished Good'
    }
    
    # Check current state
    print("1. Current state:")
    unique_types = db.session.query(ItemMaster.item_type).distinct().all()
    for (item_type,) in unique_types:
        if item_type:
            print(f"   - '{item_type}'")
    
    print()
    
    # Update the values
    print("2. Updating item types...")
    updated_count = 0
    
    for old_type, new_type in type_mapping.items():
        items = ItemMaster.query.filter_by(item_type=old_type).all()
        if items:
            print(f"   Updating {len(items)} items from '{old_type}' to '{new_type}'")
            for item in items:
                item.item_type = new_type
                updated_count += 1
    
    if updated_count > 0:
        try:
            db.session.commit()
            print(f"   ✅ Successfully updated {updated_count} items")
        except Exception as e:
            db.session.rollback()
            print(f"   ❌ Error updating items: {e}")
            return
    else:
        print("   ℹ️  No items to update")
    
    print()
    
    # Verify the changes
    print("3. Verification:")
    unique_types_after = db.session.query(ItemMaster.item_type).distinct().all()
    for (item_type,) in unique_types_after:
        if item_type:
            print(f"   - '{item_type}'")
    
    print()
    print("4. Summary:")
    print(f"   - Updated {updated_count} items")
    print("   - Item types now match ItemType table")
    print("   - Frontend should now work correctly")

if __name__ == "__main__":
    # Create app context
    from app import create_app
    app = create_app()
    
    with app.app_context():
        fix_item_types() 