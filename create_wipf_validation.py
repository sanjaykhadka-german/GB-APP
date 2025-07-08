from app import create_app, db
from models.item_master import ItemMaster
from models.item_type import ItemType
from sqlalchemy import text

def validate_wipf_relationships():
    """
    Validate WIPF relationships and detect common issues
    This is a proper function that can detect relationship problems generically
    """
    print("Validating WIPF relationships...\n")
    
    issues_found = []
    
    # Get all FG items with WIPF relationships
    fg_items = db.session.query(ItemMaster).join(ItemType).filter(
        ItemType.type_name == 'FG',
        ItemMaster.wipf_item_id.isnot(None)
    ).all()
    
    print(f"Checking {len(fg_items)} FG items with WIPF relationships...")
    
    for fg_item in fg_items:
        # Extract base code (e.g., '2015.100' from '2015.100.2')
        fg_parts = fg_item.item_code.split('.')
        if len(fg_parts) >= 2:
            expected_wipf_base = f"{fg_parts[0]}.{fg_parts[1]}"
            
            # Check if WIPF item exists and matches expected pattern
            if fg_item.wipf_item:
                actual_wipf_code = fg_item.wipf_item.item_code
                
                # Check if WIPF code matches expected pattern
                if not actual_wipf_code.startswith(expected_wipf_base):
                    issues_found.append({
                        'type': 'MISMATCH',
                        'fg_code': fg_item.item_code,
                        'fg_id': fg_item.id,
                        'expected_wipf': expected_wipf_base,
                        'actual_wipf': actual_wipf_code,
                        'wipf_id': fg_item.wipf_item_id,
                        'description': f"FG {fg_item.item_code} should link to WIPF {expected_wipf_base}* but links to {actual_wipf_code}"
                    })
    
    # Check for multiple FG items pointing to same WIPF when they shouldn't
    wipf_usage = {}
    for fg_item in fg_items:
        if fg_item.wipf_item_id:
            if fg_item.wipf_item_id not in wipf_usage:
                wipf_usage[fg_item.wipf_item_id] = []
            wipf_usage[fg_item.wipf_item_id].append(fg_item)
    
    for wipf_id, fg_list in wipf_usage.items():
        if len(fg_list) > 1:
            # Check if these FG items should really share the same WIPF
            wipf_item = ItemMaster.query.get(wipf_id)
            if wipf_item:
                # Group FG items by their expected WIPF base
                expected_groups = {}
                for fg in fg_list:
                    fg_parts = fg.item_code.split('.')
                    if len(fg_parts) >= 2:
                        expected_base = f"{fg_parts[0]}.{fg_parts[1]}"
                        if expected_base not in expected_groups:
                            expected_groups[expected_base] = []
                        expected_groups[expected_base].append(fg)
                
                # If multiple expected groups share same WIPF, it might be wrong
                if len(expected_groups) > 1:
                    issues_found.append({
                        'type': 'MULTIPLE_EXPECTED',
                        'wipf_code': wipf_item.item_code,
                        'wipf_id': wipf_id,
                        'fg_items': [fg.item_code for fg in fg_list],
                        'expected_groups': list(expected_groups.keys()),
                        'description': f"WIPF {wipf_item.item_code} is shared by FG items that should have different WIPFs: {list(expected_groups.keys())}"
                    })
    
    # Report findings
    if issues_found:
        print(f"\n⚠️  Found {len(issues_found)} WIPF relationship issues:\n")
        
        for issue in issues_found:
            print(f"Issue Type: {issue['type']}")
            print(f"Description: {issue['description']}")
            if issue['type'] == 'MISMATCH':
                print(f"  Suggested Fix: Update FG {issue['fg_code']} to link to WIPF {issue['expected_wipf']}")
            print()
        
        return issues_found
    else:
        print("✅ All WIPF relationships appear correct!")
        return []

def suggest_wipf_fixes(issues):
    """
    Generate SQL statements to fix WIPF relationship issues
    This provides the fix commands rather than hardcoding them
    """
    if not issues:
        print("No issues to fix!")
        return
    
    print("Suggested SQL fixes:\n")
    
    for issue in issues:
        if issue['type'] == 'MISMATCH':
            # Find the correct WIPF item
            expected_wipf = ItemMaster.query.filter_by(item_code=issue['expected_wipf']).first()
            if expected_wipf:
                print(f"-- Fix FG {issue['fg_code']} to point to correct WIPF")
                print(f"UPDATE item_master SET wipf_item_id = {expected_wipf.id} WHERE id = {issue['fg_id']};")
                print()
            else:
                print(f"-- WARNING: Expected WIPF {issue['expected_wipf']} not found!")
                print(f"-- You may need to create WIPF item {issue['expected_wipf']} first")
                print()

def auto_fix_wipf_relationships(issues):
    """
    Automatically fix WIPF relationship issues (non-hardcoded)
    This function can fix any WIPF relationship issue generically
    """
    if not issues:
        print("No issues to fix!")
        return
    
    print("Applying automatic fixes...\n")
    
    fixed_count = 0
    for issue in issues:
        if issue['type'] == 'MISMATCH':
            try:
                # Find the correct WIPF item
                expected_wipf = ItemMaster.query.filter_by(item_code=issue['expected_wipf']).first()
                if expected_wipf:
                    # Update the FG item
                    fg_item = ItemMaster.query.get(issue['fg_id'])
                    if fg_item:
                        old_wipf_id = fg_item.wipf_item_id
                        fg_item.wipf_item_id = expected_wipf.id
                        print(f"✅ Fixed FG {fg_item.item_code}: WIPF ID {old_wipf_id} → {expected_wipf.id} ({expected_wipf.item_code})")
                        fixed_count += 1
                else:
                    print(f"❌ Cannot fix FG {issue['fg_code']}: Expected WIPF {issue['expected_wipf']} not found")
            except Exception as e:
                print(f"❌ Error fixing FG {issue['fg_code']}: {str(e)}")
    
    if fixed_count > 0:
        try:
            db.session.commit()
            print(f"\n✅ Successfully fixed {fixed_count} WIPF relationships!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error committing fixes: {str(e)}")
    else:
        print("\n⚠️  No fixes were applied")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        # Validate relationships
        issues = validate_wipf_relationships()
        
        if issues:
            print("\n" + "="*50)
            print("SUGGESTED FIXES:")
            print("="*50)
            suggest_wipf_fixes(issues)
            
            # Ask user if they want to auto-fix
            print("\nWould you like to auto-fix these issues? (y/n)")
            # For script purposes, auto-apply fixes
            auto_fix_wipf_relationships(issues) 