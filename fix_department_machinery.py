from app import create_app, db
from models.item_master import ItemMaster
from models.item_type import ItemType
from models.department import Department
from models.machinery import Machinery

def check_missing_assignments():
    """Check for items missing department or machinery assignments"""
    items = ItemMaster.query.join(ItemType).filter(
        ItemType.type_name.in_(['FG', 'WIPF', 'WIP'])
    ).all()
    
    missing_count = 0
    for item in items:
        missing = []
        if not item.department_id:
            missing.append('department')
        if not item.machinery_id:
            missing.append('machinery')
            
        if missing:
            missing_count += 1
            print(f"Item {item.item_code} ({item.item_type.type_name}) missing: {', '.join(missing)}")
    
    return missing_count

def fix_missing_assignments():
    """Fix missing department and machinery assignments"""
    # Get default departments
    packing_dept = Department.query.filter_by(departmentName='Packing').first()
    production_dept = Department.query.filter_by(departmentName='Production').first()
    
    if not packing_dept or not production_dept:
        print("❌ Required departments not found!")
        return False
    
    # Get default machinery
    ulma = Machinery.query.filter_by(machineryName='ULMA').first()
    rex = Machinery.query.filter_by(machineryName='Rex').first()
    
    if not ulma or not rex:
        print("❌ Required machinery not found!")
        return False
    
    # Get items missing assignments
    items = ItemMaster.query.join(ItemType).filter(
        ItemType.type_name.in_(['FG', 'WIPF', 'WIP']),
        (ItemMaster.department_id.is_(None) | ItemMaster.machinery_id.is_(None))
    ).all()
    
    fixed_count = 0
    for item in items:
        changes = []
        
        # Assign department if missing
        if not item.department_id:
            if item.item_type.type_name == 'FG':
                item.department_id = packing_dept.department_id
                changes.append(f"department -> {packing_dept.departmentName}")
            else:  # WIPF or WIP
                item.department_id = production_dept.department_id
                changes.append(f"department -> {production_dept.departmentName}")
        
        # Assign machinery if missing
        if not item.machinery_id:
            if item.item_type.type_name == 'FG':
                item.machinery_id = ulma.machineID
                changes.append(f"machinery -> {ulma.machineryName}")
            else:  # WIPF or WIP
                item.machinery_id = rex.machineID
                changes.append(f"machinery -> {rex.machineryName}")
        
        if changes:
            fixed_count += 1
            print(f"Fixed {item.item_code} ({item.item_type.type_name}): {', '.join(changes)}")
    
    if fixed_count > 0:
        db.session.commit()
        print(f"\n✅ Fixed {fixed_count} items")
    else:
        print("\n✅ No items needed fixing")
    
    return True

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        print("\nChecking for missing assignments...")
        missing_count = check_missing_assignments()
        
        if missing_count > 0:
            print(f"\nFound {missing_count} items with missing assignments")
            input("\nPress Enter to fix these items...")
            fix_missing_assignments()
        else:
            print("\n✅ All items have proper assignments") 