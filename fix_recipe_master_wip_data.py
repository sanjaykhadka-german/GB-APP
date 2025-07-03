#!/usr/bin/env python3
"""
Fix recipe_master table data integrity issue.
Replace FG and RM items in recipe_wip_id with their corresponding WIP items.
"""

import os
import sys
sys.path.append('.')

from flask import Flask
from database import db
from dotenv import load_dotenv
from models.item_master import ItemMaster
from models.recipe_master import RecipeMaster
from models.item_type import ItemType
from sqlalchemy import func

# Load environment
load_dotenv()

# Create Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def analyze_current_state():
    """Analyze the current state of recipe_master data"""
    print("🔍 Current state analysis:")
    
    type_counts = db.session.query(
        ItemType.type_name,
        func.count(RecipeMaster.id).label('count')
    ).join(
        ItemMaster, RecipeMaster.recipe_wip_id == ItemMaster.id
    ).join(
        ItemType, ItemMaster.item_type_id == ItemType.id
    ).group_by(ItemType.type_name).all()
    
    for type_name, count in type_counts:
        status = "✅ CORRECT" if type_name == 'WIP' else "❌ WRONG"
        print(f"  - {type_name}: {count} recipes {status}")
    
    return type_counts

def fix_fg_to_wip():
    """Fix FG items by replacing them with their WIP mappings"""
    print("\n🔧 Fixing FG items to WIP...")
    
    # Get all FG items used as recipe codes that have WIP mappings
    fg_items_to_fix = db.session.query(
        RecipeMaster.id,
        ItemMaster.item_code.label('fg_code'),
        ItemMaster.wip_item_id,
        ItemMaster.id.label('fg_id')
    ).join(
        ItemMaster, RecipeMaster.recipe_wip_id == ItemMaster.id
    ).join(
        ItemType, ItemMaster.item_type_id == ItemType.id
    ).filter(
        ItemType.type_name == 'FG',
        ItemMaster.wip_item_id.isnot(None)
    ).all()
    
    print(f"Found {len(fg_items_to_fix)} FG recipes with WIP mappings")
    
    fixed_count = 0
    mapping_summary = {}
    
    for recipe_id, fg_code, wip_item_id, fg_id in fg_items_to_fix:
        # Get the WIP item
        wip_item = db.session.get(ItemMaster, wip_item_id)
        if wip_item:
            # Update the recipe to use WIP item instead of FG
            recipe = db.session.get(RecipeMaster, recipe_id)
            if recipe:
                old_id = recipe.recipe_wip_id
                recipe.recipe_wip_id = wip_item_id
                
                # Track the mapping for summary
                mapping_key = f"{fg_code} -> {wip_item.item_code}"
                mapping_summary[mapping_key] = mapping_summary.get(mapping_key, 0) + 1
                
                fixed_count += 1
    
    print(f"Fixed {fixed_count} FG recipes")
    print("FG -> WIP mappings applied:")
    for mapping, count in mapping_summary.items():
        print(f"  - {mapping} ({count} recipes)")
    
    return fixed_count

def fix_rm_items():
    """Check RM items - these might need special handling"""
    print("\n🔧 Checking RM items...")
    
    rm_items = db.session.query(
        ItemMaster.item_code,
        ItemMaster.description,
        func.count(RecipeMaster.id).label('recipe_count')
    ).join(
        RecipeMaster, RecipeMaster.recipe_wip_id == ItemMaster.id
    ).join(
        ItemType, ItemMaster.item_type_id == ItemType.id
    ).filter(
        ItemType.type_name == 'RM'
    ).group_by(ItemMaster.item_code, ItemMaster.description).all()
    
    print(f"Found {len(rm_items)} RM items used as recipe codes:")
    for rm_code, rm_desc, count in rm_items:
        print(f"  - {rm_code}: {rm_desc} ({count} recipes)")
    
    print("⚠️  RM items need manual review - they might be incorrectly classified")
    print("   Consider checking if these should be WIP items instead")
    
    return len(rm_items)

def verify_fix():
    """Verify that the fix worked correctly"""
    print("\n✅ Verification after fix:")
    
    type_counts = db.session.query(
        ItemType.type_name,
        func.count(RecipeMaster.id).label('count')
    ).join(
        ItemMaster, RecipeMaster.recipe_wip_id == ItemMaster.id
    ).join(
        ItemType, ItemMaster.item_type_id == ItemType.id
    ).group_by(ItemType.type_name).all()
    
    wip_count = 0
    total_count = 0
    
    for type_name, count in type_counts:
        total_count += count
        if type_name == 'WIP':
            wip_count = count
        status = "✅ CORRECT" if type_name == 'WIP' else "❌ STILL WRONG"
        print(f"  - {type_name}: {count} recipes {status}")
    
    improvement = wip_count - 50  # Original WIP count was 50
    print(f"\n📊 Improvement: +{improvement} recipes now use correct WIP items")
    print(f"   WIP coverage: {wip_count}/{total_count} ({wip_count/total_count*100:.1f}%)")
    
    return wip_count, total_count

def main():
    """Main execution function"""
    print("🚀 Fixing Recipe Master Data Integrity")
    print("=" * 50)
    print("Problem: recipe_wip_id contains FG and RM items instead of WIP only")
    print("Solution: Replace with corresponding WIP items where mappings exist")
    print("=" * 50)
    
    with app.app_context():
        # 1. Analyze current state
        analyze_current_state()
        
        # 2. Fix FG items
        fixed_fg = fix_fg_to_wip()
        
        # 3. Check RM items
        rm_count = fix_rm_items()
        
        # 4. Commit the changes
        if fixed_fg > 0:
            print(f"\n💾 Committing {fixed_fg} fixes to database...")
            db.session.commit()
            print("✅ Changes committed successfully")
        else:
            print("\n⚠️  No changes to commit")
        
        # 5. Verify the fix
        wip_count, total_count = verify_fix()
        
        print("\n" + "=" * 50)
        print("🎉 Recipe Master Fix Complete!")
        print(f"✅ Fixed {fixed_fg} FG recipes to use WIP items")
        print(f"⚠️  {rm_count} RM items still need manual review")
        print(f"📈 WIP coverage improved to {wip_count}/{total_count} recipes")
        
        remaining_issues = total_count - wip_count
        if remaining_issues > 0:
            print(f"📝 Next steps: Review {remaining_issues} remaining non-WIP recipes")
        else:
            print("🎊 All recipes now use WIP items correctly!")

if __name__ == "__main__":
    main() 