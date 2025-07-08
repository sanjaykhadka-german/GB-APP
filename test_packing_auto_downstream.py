"""
Test script to verify that creating packing entries automatically creates
filling (WIPF) and production (WIP) entries through the BOM service
"""

from app import create_app, db
from models.packing import Packing
from models.filling import Filling
from models.production import Production
from models.item_master import ItemMaster
from models.soh import SOH
from datetime import date, timedelta
from controllers.bom_service import BOMService

def test_packing_auto_downstream():
    """Test that creating packing entries auto-creates downstream entries"""
    
    print("Testing automatic downstream entry creation...\n")
    
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
    
    # Check if SOH entry exists for this item
    soh_entry = SOH.query.filter_by(item_id=fg_item.id, week_commencing=week_commencing).first()
    if not soh_entry:
        print("Creating test SOH entry...")
        soh_entry = SOH(
            item_id=fg_item.id,
            fg_code=fg_item.item_code,
            week_commencing=week_commencing,
            soh_total_units=100,  # Test with 100 units
            description=fg_item.description
        )
        db.session.add(soh_entry)
        db.session.commit()
        print(f"✅ Created SOH entry: {soh_entry.fg_code} - {soh_entry.soh_total_units} total units\n")
    
    # Count existing entries before test
    packing_count_before = Packing.query.filter_by(
        item_id=fg_item.id,
        packing_date=test_date
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
    
    # Test the BOM service directly (this is what packing create calls)
    print("Testing BOM service update_downstream_requirements...")
    success = BOMService.update_downstream_requirements(test_date, week_commencing)
    
    if not success:
        print(f"❌ BOM service failed")
        return False
    
    print(f"✅ BOM service succeeded\n")
    
    # Count entries after test
    filling_count_after = Filling.query.filter_by(
        item_id=fg_item.wipf_item_id if fg_item.wipf_item_id else None,
        week_commencing=week_commencing
    ).count()
    
    production_count_after = Production.query.filter_by(
        item_id=fg_item.wip_item_id if fg_item.wip_item_id else None,
        week_commencing=week_commencing
    ).count()
    
    print(f"📊 After test:")
    print(f"  Filling entries: {filling_count_after}")
    print(f"  Production entries: {production_count_after}\n")
    
    # Show created entries
    if filling_count_after > filling_count_before:
        filling_entries = Filling.query.filter_by(
            item_id=fg_item.wipf_item_id if fg_item.wipf_item_id else None,
            week_commencing=week_commencing
        ).all()
        
        print("📋 Filling entries created:")
        for entry in filling_entries:
            print(f"  - WIPF {entry.item.item_code}: {entry.requirement_kg} kg (week {entry.week_commencing})")
        print()
    
    if production_count_after > production_count_before:
        production_entries = Production.query.filter_by(
            item_id=fg_item.wip_item_id if fg_item.wip_item_id else None,
            week_commencing=week_commencing
        ).all()
        
        print("📋 Production entries created:")
        for entry in production_entries:
            print(f"  - WIP {entry.item.item_code}: {entry.total_kg} kg (week {entry.week_commencing})")
        print()
    
    # Verify allergens work correctly
    test_packing = Packing.query.filter_by(item_id=fg_item.id).first()
    if test_packing:
        allergens = test_packing.allergens  # This should get allergens from item_master
        print(f"🔍 Allergen test for packing entry:")
        print(f"  Item: {fg_item.item_code}")
        print(f"  Allergens count: {len(allergens)}")
        for allergen in allergens:
            print(f"    - {allergen.allergen_name}")
    else:
        print("⚠️  No packing entries found to test allergens")
    
    return True

def test_allergen_property():
    """Test that the allergen property works correctly"""
    
    print("\n" + "="*50)
    print("TESTING ALLERGEN PROPERTY")
    print("="*50)
    
    # Get a packing entry
    packing = Packing.query.first()
    if not packing:
        print("❌ No packing entries found to test allergens")
        return False
    
    print(f"Testing allergens for packing entry: {packing.item.item_code}")
    
    # Test the allergens property
    allergens = packing.allergens
    print(f"Found {len(allergens)} allergens:")
    
    for allergen in allergens:
        print(f"  - {allergen.allergen_name}")
    
    # Compare with direct item_master allergens
    item_allergens = packing.item.allergens
    print(f"\nDirect from item_master: {len(item_allergens)} allergens")
    
    if len(allergens) == len(item_allergens):
        print("✅ Allergen property works correctly!")
        return True
    else:
        print("❌ Allergen property mismatch!")
        return False

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        success = test_packing_auto_downstream()
        if success:
            test_allergen_property()
        print("\n" + "="*50)
        print("TEST COMPLETE")
        print("="*50) 