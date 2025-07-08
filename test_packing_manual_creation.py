"""
Test script to manually create a packing entry and verify
that filling and production entries are automatically created
"""

from app import create_app, db
from models.packing import Packing
from models.filling import Filling
from models.production import Production
from models.item_master import ItemMaster
from models.soh import SOH
from datetime import date, timedelta

def test_manual_packing_creation():
    """Test creating a packing entry and verify auto-downstream creation"""
    
    print("Testing manual packing creation with auto-downstream...\n")
    
    # Test parameters
    test_date = date.today()
    week_commencing = test_date - timedelta(days=test_date.weekday())  # Get Monday
    
    # Get a test FG item that has WIPF and WIP relationships
    fg_item = db.session.query(ItemMaster).join(ItemMaster.item_type).filter(
        ItemMaster.item_type.has(type_name='FG'),
        ItemMaster.wipf_item_id.isnot(None),
        ItemMaster.wip_item_id.isnot(None)
    ).first()
    
    if not fg_item:
        print("❌ No FG item found with both WIPF and WIP relationships!")
        return False
    
    print(f"Testing with FG item: {fg_item.item_code} ({fg_item.description})")
    print(f"  WIPF: {fg_item.wipf_item.item_code if fg_item.wipf_item else 'None'}")
    print(f"  WIP: {fg_item.wip_item.item_code if fg_item.wip_item else 'None'}")
    print(f"  Test date: {test_date}")
    print(f"  Week commencing: {week_commencing}\n")
    
    # Ensure SOH entry exists
    soh_entry = SOH.query.filter_by(item_id=fg_item.id, week_commencing=week_commencing).first()
    if not soh_entry:
        print("Creating SOH entry...")
        soh_entry = SOH(
            item_id=fg_item.id,
            fg_code=fg_item.item_code,
            week_commencing=week_commencing,
            soh_total_units=50,  # Test with 50 units SOH
            description=fg_item.description
        )
        db.session.add(soh_entry)
        db.session.commit()
        print(f"✅ Created SOH entry: {soh_entry.fg_code} - {soh_entry.soh_total_units} total units\n")
    
    # Count existing entries before test
    packing_count_before = Packing.query.filter_by(
        item_id=fg_item.id,
        packing_date=test_date,
        week_commencing=week_commencing
    ).count()
    
    filling_count_before = Filling.query.filter_by(
        item_id=fg_item.wipf_item_id if fg_item.wipf_item_id else None,
        week_commencing=week_commencing
    ).count()
    
    production_count_before = Production.query.filter_by(
        item_id=fg_item.wip_item_id if fg_item.wip_item_id else None,
        week_commencing=week_commencing
    ).count()
    
    print(f"📊 Before test:")
    print(f"  Packing entries: {packing_count_before}")
    print(f"  Filling entries: {filling_count_before}")
    print(f"  Production entries: {production_count_before}\n")
    
    # Create a test packing entry manually (simulate what the web form does)
    print("Creating packing entry manually...")
    
    # Calculate some basic values
    avg_weight = fg_item.avg_weight_per_unit or fg_item.kg_per_unit or 1.0
    min_level = fg_item.min_level or 0.0
    max_level = fg_item.max_level or 200.0  # Set a reasonable max level
    calc_factor = fg_item.calculation_factor or 1.0
    
    # Calculate requirements (simulating packing controller logic)
    soh_units = soh_entry.soh_total_units
    soh_requirement_units = int(max_level - soh_units) if soh_units < min_level else 100  # Force some requirement
    soh_requirement_kg = soh_requirement_units * avg_weight
    requirement_kg = soh_requirement_kg * calc_factor
    
    print(f"Calculated values:")
    print(f"  SOH units: {soh_units}")
    print(f"  Requirement units: {soh_requirement_units}")
    print(f"  Requirement kg: {requirement_kg}")
    print(f"  Avg weight per unit: {avg_weight}")
    
    # Create the packing entry
    new_packing = Packing(
        packing_date=test_date,
        item_id=fg_item.id,
        week_commencing=week_commencing,
        requirement_kg=requirement_kg,
        requirement_unit=soh_requirement_units,
        soh_requirement_kg_week=soh_requirement_kg,
        soh_requirement_units_week=soh_requirement_units,
        soh_kg=soh_units * avg_weight,
        soh_units=soh_units,
        avg_weight_per_unit=avg_weight,
        calculation_factor=calc_factor,
        machinery_id=fg_item.machinery_id,
        department_id=fg_item.department_id
    )
    
    db.session.add(new_packing)
    db.session.commit()
    print(f"✅ Created packing entry: ID {new_packing.id}\n")
    
    # Now test the auto-downstream creation using the same function as the web interface
    print("Testing auto-downstream creation...")
    from controllers.packing_controller import re_aggregate_filling_and_production_for_date
    
    success, message = re_aggregate_filling_and_production_for_date(test_date, week_commencing)
    
    if success:
        print(f"✅ {message}\n")
    else:
        print(f"❌ {message}\n")
    
    # Count entries after test
    packing_count_after = Packing.query.filter_by(
        item_id=fg_item.id,
        packing_date=test_date,
        week_commencing=week_commencing
    ).count()
    
    filling_count_after = Filling.query.filter_by(
        item_id=fg_item.wipf_item_id if fg_item.wipf_item_id else None,
        week_commencing=week_commencing
    ).count()
    
    production_count_after = Production.query.filter_by(
        item_id=fg_item.wip_item_id if fg_item.wip_item_id else None,
        week_commencing=week_commencing
    ).count()
    
    print(f"📊 After test:")
    print(f"  Packing entries: {packing_count_after}")
    print(f"  Filling entries: {filling_count_after}")
    print(f"  Production entries: {production_count_after}\n")
    
    # Show what was created
    if filling_count_after > filling_count_before:
        filling_entries = Filling.query.filter_by(
            item_id=fg_item.wipf_item_id,
            week_commencing=week_commencing
        ).all()
        
        print("📋 Filling entries created:")
        for entry in filling_entries:
            print(f"  - WIPF {entry.item.item_code}: {entry.requirement_kg} kg (week {entry.week_commencing})")
        print()
    
    if production_count_after > production_count_before:
        production_entries = Production.query.filter_by(
            item_id=fg_item.wip_item_id,
            week_commencing=week_commencing
        ).all()
        
        print("📋 Production entries created:")
        for entry in production_entries:
            print(f"  - WIP {entry.item.item_code}: {entry.total_kg} kg (week {entry.week_commencing})")
        print()
    
    # Test allergens
    print("🔍 Testing allergen property:")
    allergens = new_packing.allergens
    print(f"  Packing entry allergens: {len(allergens)}")
    for allergen in allergens:
        print(f"    - {allergen.allergen_name}")
    
    return True

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        test_manual_packing_creation()
        print("\n" + "="*50)
        print("TEST COMPLETE")
        print("="*50) 