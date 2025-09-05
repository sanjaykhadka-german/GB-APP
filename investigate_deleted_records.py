#!/usr/bin/env python3
"""
Investigate Deleted ItemMaster Records
Find traces of the deleted WIP and component items that caused orphaned RecipeMaster records
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def investigate_deleted_records():
    """Investigate what ItemMaster records were deleted"""
    
    with app.app_context():
        try:
            print("🔍 Investigating deleted ItemMaster records...")
            print("=" * 60)
            
            # The orphaned RecipeMaster records referenced these IDs:
            deleted_wip_id = 277
            deleted_component_ids = [81, 103, 63, 139]
            
            print(f"\n📊 Orphaned RecipeMaster records referenced:")
            print(f"   WIP Item ID: {deleted_wip_id}")
            print(f"   Component Item IDs: {deleted_component_ids}")
            
            # Check if these IDs exist in item_master
            print(f"\n🔍 Checking if these IDs still exist in item_master:")
            
            # Check WIP item
            wip_exists = db.session.execute(text(f"SELECT COUNT(*) as count FROM item_master WHERE id = {deleted_wip_id}")).fetchone()
            print(f"   Item ID {deleted_wip_id}: {'EXISTS' if wip_exists.count > 0 else 'DELETED'}")
            
            # Check component items
            for comp_id in deleted_component_ids:
                comp_exists = db.session.execute(text(f"SELECT COUNT(*) as count FROM item_master WHERE id = {comp_id}")).fetchone()
                print(f"   Item ID {comp_id}: {'EXISTS' if comp_exists.count > 0 else 'DELETED'}")
            
            # Look for traces in other tables
            print(f"\n📋 Looking for traces of deleted item {deleted_wip_id} in other tables:")
            
            # Check SOH table
            soh_refs = db.session.execute(text(f"SELECT COUNT(*) as count FROM soh WHERE item_id = {deleted_wip_id}")).fetchone()
            print(f"   SOH references: {soh_refs.count}")
            
            # Check packing table
            packing_refs = db.session.execute(text(f"SELECT COUNT(*) as count FROM packing WHERE item_id = {deleted_wip_id}")).fetchone()
            print(f"   Packing references: {packing_refs.count}")
            
            # Check filling table
            filling_refs = db.session.execute(text(f"SELECT COUNT(*) as count FROM filling WHERE item_id = {deleted_wip_id}")).fetchone()
            print(f"   Filling references: {filling_refs.count}")
            
            # Check production table
            production_refs = db.session.execute(text(f"SELECT COUNT(*) as count FROM production WHERE item_id = {deleted_wip_id}")).fetchone()
            print(f"   Production references: {production_refs.count}")
            
            # Check if there are any items with similar codes that might give us clues
            print(f"\n🔍 Looking for similar item codes that might be related:")
            
            # Look for items with WIP in the code
            wip_items = db.session.execute(text("""
                SELECT id, item_code, description, item_type_id 
                FROM item_master 
                WHERE item_code LIKE '%WIP%' 
                OR description LIKE '%WIP%'
                ORDER BY id
            """)).fetchall()
            
            print(f"   Items with 'WIP' in code/description:")
            for item in wip_items:
                print(f"     ID: {item.id}, Code: {item.item_code}, Description: {item.description}, Type ID: {item.item_type_id}")
            
            # Look for items with HAM in the description
            ham_items = db.session.execute(text("""
                SELECT id, item_code, description, item_type_id 
                FROM item_master 
                WHERE description LIKE '%HAM%' 
                OR item_code LIKE '%HAM%'
                ORDER BY id
            """)).fetchall()
            
            print(f"\n   Items with 'HAM' in code/description:")
            for item in ham_items:
                print(f"     ID: {item.id}, Code: {item.item_code}, Description: {item.description}, Type ID: {item.item_type_id}")
            
            # Check the current max ID to see if there's a gap around 277
            print(f"\n📈 Checking ID ranges:")
            max_id = db.session.execute(text("SELECT MAX(id) as max_id FROM item_master")).fetchone()
            print(f"   Current max item_master ID: {max_id.max_id}")
            
            # Check for gaps around ID 277
            items_around_277 = db.session.execute(text("""
                SELECT id, item_code, description, item_type_id
                FROM item_master 
                WHERE id BETWEEN 270 AND 285
                ORDER BY id
            """)).fetchall()
            
            print(f"\n   Items around ID 277 (270-285):")
            for item in items_around_277:
                print(f"     ID: {item.id}, Code: {item.item_code}, Description: {item.description}, Type ID: {item.item_type_id}")
            
            # Check for gaps around component IDs
            print(f"\n   Items around component IDs (75-145):")
            items_around_components = db.session.execute(text("""
                SELECT id, item_code, description, item_type_id
                FROM item_master 
                WHERE id BETWEEN 75 AND 145
                ORDER BY id
            """)).fetchall()
            
            for item in items_around_components:
                print(f"     ID: {item.id}, Code: {item.item_code}, Description: {item.description}, Type ID: {item.item_type_id}")
            
            # Look for any remaining references to the deleted IDs in string fields
            print(f"\n🔍 Looking for string references to deleted IDs:")
            
            # Check if any tables have string references to these IDs
            tables_to_check = ['soh', 'packing', 'filling', 'production']
            
            for table in tables_to_check:
                try:
                    # Check if table has fg_code, product_code, fill_code, or production_code columns
                    columns_query = text(f"""
                        SELECT COLUMN_NAME 
                        FROM INFORMATION_SCHEMA.COLUMNS 
                        WHERE TABLE_SCHEMA = DATABASE() 
                        AND TABLE_NAME = '{table}'
                        AND COLUMN_NAME IN ('fg_code', 'product_code', 'fill_code', 'production_code')
                    """)
                    
                    columns = db.session.execute(columns_query).fetchall()
                    
                    for col in columns:
                        col_name = col.COLUMN_NAME
                        # Look for any string references that might contain the deleted item codes
                        refs_query = text(f"""
                            SELECT DISTINCT {col_name} as ref_value
                            FROM {table} 
                            WHERE {col_name} IS NOT NULL 
                            AND {col_name} != ''
                            ORDER BY {col_name}
                        """)
                        
                        refs = db.session.execute(refs_query).fetchall()
                        print(f"   {table}.{col_name} values:")
                        for ref in refs[:10]:  # Show first 10 values
                            print(f"     {ref.ref_value}")
                        if len(refs) > 10:
                            print(f"     ... and {len(refs) - 10} more")
                            
                except Exception as e:
                    print(f"   Error checking {table}: {str(e)}")
            
            # Check item types to understand what type of items were deleted
            print(f"\n📋 Item types in the system:")
            item_types = db.session.execute(text("""
                SELECT id, type_name, description
                FROM item_type
                ORDER BY id
            """)).fetchall()
            
            for item_type in item_types:
                print(f"   ID: {item_type.id}, Type: {item_type.type_name}, Description: {item_type.description}")
            
            print(f"\n" + "=" * 60)
            print("✅ Investigation completed!")
            
        except Exception as e:
            logger.error(f"❌ Error during investigation: {str(e)}")
            raise

if __name__ == '__main__':
    investigate_deleted_records()
