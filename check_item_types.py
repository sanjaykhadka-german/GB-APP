#!/usr/bin/env python3
"""
Script to check item types in the database and identify any mismatches
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from database import db
from models.item_type import ItemType
from models.item_master import ItemMaster

def check_item_types():
    print("Checking Item Types in Database...")
    print("=" * 50)
    
    # Check ItemType table
    print("1. ItemType table contents:")
    item_types = ItemType.query.all()
    if item_types:
        for item_type in item_types:
            print(f"   - ID: {item_type.id}, Name: '{item_type.type_name}'")
    else:
        print("   No item types found in ItemType table")
    
    print()
    
    # Check ItemMaster table for unique item_type values
    print("2. Unique item_type values in ItemMaster table:")
    unique_types = db.session.query(ItemMaster.item_type).distinct().all()
    if unique_types:
        for (item_type,) in unique_types:
            if item_type:
                print(f"   - '{item_type}'")
            else:
                print("   - NULL/Empty")
    else:
        print("   No items found in ItemMaster table")
    
    print()
    
    # Check for mismatches
    print("3. Checking for mismatches:")
    item_type_names = [it.type_name for it in item_types]
    master_types = [mt[0] for mt in unique_types if mt[0]]
    
    print(f"   ItemType table names: {item_type_names}")
    print(f"   ItemMaster table types: {master_types}")
    
    # Find types in ItemMaster that don't exist in ItemType
    missing_in_itemtype = set(master_types) - set(item_type_names)
    if missing_in_itemtype:
        print(f"   ⚠️  Types in ItemMaster but not in ItemType: {missing_in_itemtype}")
    else:
        print("   ✅ All ItemMaster types exist in ItemType table")
    
    # Find types in ItemType that aren't used in ItemMaster
    unused_in_itemtype = set(item_type_names) - set(master_types)
    if unused_in_itemtype:
        print(f"   ℹ️  Types in ItemType but not used in ItemMaster: {unused_in_itemtype}")
    else:
        print("   ✅ All ItemType entries are used in ItemMaster")
    
    print()
    print("4. Recommendations:")
    if missing_in_itemtype:
        print("   - Add missing item types to ItemType table")
        for missing_type in missing_in_itemtype:
            print(f"     INSERT INTO item_type (type_name) VALUES ('{missing_type}');")
    
    if not item_types:
        print("   - ItemType table is empty, consider adding default types:")
        print("     INSERT INTO item_type (type_name) VALUES ('Raw Material');")
        print("     INSERT INTO item_type (type_name) VALUES ('Finished Good');")

if __name__ == "__main__":
    # Create app context
    from app import create_app
    app = create_app()
    
    with app.app_context():
        check_item_types() 