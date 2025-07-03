#!/usr/bin/env python3
"""
Populate WIP and WIPF relationships in ItemMaster table.
This script fills the wip_item_id and wipf_item_id columns for Finished Goods
based on existing data in the joining table and other relationships.
"""

import os
import sys
from flask import Flask
from database import db
from dotenv import load_dotenv
from sqlalchemy import text
from models.item_master import ItemMaster
from models.joining import Joining

def setup_app():
    """Setup Flask app with database configuration."""
    load_dotenv()
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def analyze_current_state():
    """Analyze the current state of relationships."""
    print("🔍 Analyzing current state...")
    
    # Check FG items
    fg_query = text("""
        SELECT COUNT(*) as total, 
               COUNT(wip_item_id) as with_wip, 
               COUNT(wipf_item_id) as with_wipf 
        FROM item_master 
        WHERE item_type_id = (SELECT id FROM item_type WHERE type_name = 'FG')
    """)
    fg_result = db.session.execute(fg_query).fetchone()
    print(f"📊 FG items: {fg_result[0]} total, {fg_result[1]} have wip_item_id, {fg_result[2]} have wipf_item_id")
    
    # Check if joining table exists
    tables_query = text("SHOW TABLES LIKE 'joining'")
    tables_result = db.session.execute(tables_query).fetchall()
    joining_exists = len(tables_result) > 0
    print(f"📋 Joining table exists: {joining_exists}")
    
    if joining_exists:
        joining_count = db.session.execute(text("SELECT COUNT(*) FROM joining")).fetchone()[0]
        print(f"📋 Joining table has {joining_count} records")
    
    # Check item types
    item_types_query = text("""
        SELECT it.type_name, COUNT(im.id) as count
        FROM item_type it
        LEFT JOIN item_master im ON it.id = im.item_type_id
        GROUP BY it.id, it.type_name
        ORDER BY it.type_name
    """)
    item_types = db.session.execute(item_types_query).fetchall()
    print("📊 Item types distribution:")
    for item_type in item_types:
        print(f"   - {item_type[0]}: {item_type[1]} items")
    
    return fg_result, joining_exists

def populate_from_joining_table():
    """Populate wip_item_id and wipf_item_id from joining table."""
    print("\n🔄 Populating relationships from joining table...")
    
    # Get all active joining records
    joining_records = db.session.execute(text("""
        SELECT fg_code, filling_code, production_code
        FROM joining 
        WHERE is_active = 1
    """)).fetchall()
    
    updated_count = 0
    
    for record in joining_records:
        fg_code, filling_code, production_code = record
        
        try:
            # Get the FG item
            fg_item = db.session.execute(text("""
                SELECT id FROM item_master 
                WHERE item_code = :fg_code 
                AND item_type_id = (SELECT id FROM item_type WHERE type_name = 'FG')
            """), {"fg_code": fg_code}).fetchone()
            
            if not fg_item:
                print(f"⚠️  FG item not found: {fg_code}")
                continue
            
            fg_id = fg_item[0]
            wip_id = None
            wipf_id = None
            
            # Find WIP item (production_code)
            if production_code:
                wip_item = db.session.execute(text("""
                    SELECT id FROM item_master 
                    WHERE item_code = :production_code 
                    AND item_type_id = (SELECT id FROM item_type WHERE type_name = 'WIP')
                """), {"production_code": production_code}).fetchone()
                
                if wip_item:
                    wip_id = wip_item[0]
                else:
                    print(f"⚠️  WIP item not found: {production_code}")
            
            # Find WIPF item (filling_code)
            if filling_code:
                wipf_item = db.session.execute(text("""
                    SELECT id FROM item_master 
                    WHERE item_code = :filling_code 
                    AND item_type_id = (SELECT id FROM item_type WHERE type_name = 'WIPF')
                """), {"filling_code": filling_code}).fetchone()
                
                if wipf_item:
                    wipf_id = wipf_item[0]
                else:
                    print(f"⚠️  WIPF item not found: {filling_code}")
            
            # Update the FG item if we found any relationships
            if wip_id or wipf_id:
                update_query = text("""
                    UPDATE item_master 
                    SET wip_item_id = :wip_id, wipf_item_id = :wipf_id
                    WHERE id = :fg_id
                """)
                
                db.session.execute(update_query, {
                    "wip_id": wip_id,
                    "wipf_id": wipf_id,
                    "fg_id": fg_id
                })
                
                updated_count += 1
                
                wip_info = f"WIP: {production_code}" if wip_id else "WIP: None"
                wipf_info = f"WIPF: {filling_code}" if wipf_id else "WIPF: None"
                print(f"✅ Updated {fg_code} -> {wip_info}, {wipf_info}")
            
        except Exception as e:
            print(f"❌ Error processing {fg_code}: {str(e)}")
            continue
    
    db.session.commit()
    print(f"\n✅ Updated {updated_count} FG items with relationships")

def populate_from_recipe_patterns():
    """Try to populate relationships based on recipe patterns."""
    print("\n🔄 Analyzing recipe patterns for additional relationships...")
    
    # Look for FG items that still don't have relationships
    unlinked_fg = db.session.execute(text("""
        SELECT id, item_code, description
        FROM item_master 
        WHERE item_type_id = (SELECT id FROM item_type WHERE type_name = 'FG')
        AND wip_item_id IS NULL 
        AND wipf_item_id IS NULL
    """)).fetchall()
    
    print(f"📊 Found {len(unlinked_fg)} FG items without relationships")
    
    if len(unlinked_fg) > 0:
        print("🔍 These FG items need manual relationship setup:")
        for fg in unlinked_fg:
            print(f"   - {fg[1]}: {fg[2]}")
    
    # Look for potential WIP matches based on similar codes
    updated_count = 0
    
    for fg in unlinked_fg:
        fg_id, fg_code, fg_description = fg
        
        # Try to find WIP with similar code (common pattern: FG code might match WIP code)
        potential_wip = db.session.execute(text("""
            SELECT id, item_code FROM item_master 
            WHERE item_type_id = (SELECT id FROM item_type WHERE type_name = 'WIP')
            AND (item_code = :fg_code 
                 OR item_code LIKE CONCAT(:fg_code, '%')
                 OR :fg_code LIKE CONCAT(item_code, '%'))
        """), {"fg_code": fg_code}).fetchone()
        
        if potential_wip:
            wip_id, wip_code = potential_wip
            
            # Update the FG item
            db.session.execute(text("""
                UPDATE item_master 
                SET wip_item_id = :wip_id
                WHERE id = :fg_id
            """), {"wip_id": wip_id, "fg_id": fg_id})
            
            updated_count += 1
            print(f"✅ Linked {fg_code} -> WIP: {wip_code} (pattern match)")
    
    if updated_count > 0:
        db.session.commit()
        print(f"\n✅ Updated {updated_count} additional FG items using pattern matching")

def verify_results():
    """Verify the results of the population."""
    print("\n🔍 Verifying results...")
    
    # Check final state
    final_query = text("""
        SELECT COUNT(*) as total, 
               COUNT(wip_item_id) as with_wip, 
               COUNT(wipf_item_id) as with_wipf,
               COUNT(CASE WHEN wip_item_id IS NOT NULL OR wipf_item_id IS NOT NULL THEN 1 END) as with_any
        FROM item_master 
        WHERE item_type_id = (SELECT id FROM item_type WHERE type_name = 'FG')
    """)
    final_result = db.session.execute(final_query).fetchone()
    
    print(f"📊 Final state - FG items:")
    print(f"   - Total: {final_result[0]}")
    print(f"   - With WIP relationship: {final_result[1]}")
    print(f"   - With WIPF relationship: {final_result[2]}")
    print(f"   - With any relationship: {final_result[3]}")
    print(f"   - Still unlinked: {final_result[0] - final_result[3]}")
    
    # Show some examples of the relationships
    examples_query = text("""
        SELECT 
            fg.item_code as fg_code,
            fg.description as fg_desc,
            wip.item_code as wip_code,
            wipf.item_code as wipf_code
        FROM item_master fg
        LEFT JOIN item_master wip ON fg.wip_item_id = wip.id
        LEFT JOIN item_master wipf ON fg.wipf_item_id = wipf.id
        WHERE fg.item_type_id = (SELECT id FROM item_type WHERE type_name = 'FG')
        AND (fg.wip_item_id IS NOT NULL OR fg.wipf_item_id IS NOT NULL)
        LIMIT 10
    """)
    
    examples = db.session.execute(examples_query).fetchall()
    
    if examples:
        print(f"\n📋 Sample relationships:")
        for example in examples:
            fg_code, fg_desc, wip_code, wipf_code = example
            wip_info = wip_code if wip_code else "None"
            wipf_info = wipf_code if wipf_code else "None"
            print(f"   - {fg_code}: WIP={wip_info}, WIPF={wipf_info}")

def main():
    """Main function to populate WIP and WIPF relationships."""
    print("🚀 Starting WIP/WIPF relationship population...")
    
    app = setup_app()
    
    with app.app_context():
        try:
            # Analyze current state
            fg_result, joining_exists = analyze_current_state()
            
            if fg_result[0] == 0:
                print("❌ No FG items found. Please check your item_type configuration.")
                return
            
            # Populate from joining table if it exists
            if joining_exists:
                populate_from_joining_table()
            else:
                print("⚠️  No joining table found. Skipping joining table population.")
            
            # Try pattern-based population for remaining items
            populate_from_recipe_patterns()
            
            # Verify results
            verify_results()
            
            print("\n✅ WIP/WIPF relationship population completed!")
            print("\n💡 Next steps:")
            print("   1. Review the unlinked FG items and manually set their relationships if needed")
            print("   2. Verify the automatically created relationships are correct")
            print("   3. Consider adding business rules to validate the relationships")
            
        except Exception as e:
            print(f"❌ Error during population: {str(e)}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    main() 