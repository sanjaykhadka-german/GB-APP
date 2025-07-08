from app import create_app, db
from models.item_master import ItemMaster
from models.item_type import ItemType
from models.packing import Packing
from models.filling import Filling
from sqlalchemy import func

def check_2015_relationships():
    """Check 2015 item relationships and why 2015.100 WIPF is missing"""
    print("Checking 2015 item relationships...\n")
    
    # 1. Check if FG items exist
    print("1. Checking FG items:")
    fg_items = ['2015.125.02', '2015.100.2']
    
    for fg_code in fg_items:
        fg_item = ItemMaster.query.filter_by(item_code=fg_code).first()
        if fg_item:
            print(f"   ✓ FG {fg_code} exists (ID: {fg_item.id})")
            print(f"     Description: {fg_item.description}")
            print(f"     WIP Item ID: {fg_item.wip_item_id}")
            print(f"     WIPF Item ID: {fg_item.wipf_item_id}")
            
            # Check WIP relationship
            if fg_item.wip_item:
                print(f"     WIP Item: {fg_item.wip_item.item_code} ({fg_item.wip_item.description})")
            else:
                print(f"     ✗ No WIP relationship found")
                
            # Check WIPF relationship
            if fg_item.wipf_item:
                print(f"     WIPF Item: {fg_item.wipf_item.item_code} ({fg_item.wipf_item.description})")
            else:
                print(f"     ✗ No WIPF relationship found")
                
        else:
            print(f"   ✗ FG {fg_code} NOT found")
        print()
    
    # 2. Check if WIPF items exist
    print("2. Checking WIPF items:")
    wipf_items = ['2015.100', '2015.125']
    
    for wipf_code in wipf_items:
        wipf_item = ItemMaster.query.filter_by(item_code=wipf_code).first()
        if wipf_item:
            print(f"   ✓ WIPF {wipf_code} exists (ID: {wipf_item.id})")
            print(f"     Description: {wipf_item.description}")
            print(f"     Item Type: {wipf_item.item_type.type_name if wipf_item.item_type else 'None'}")
        else:
            print(f"   ✗ WIPF {wipf_code} NOT found")
        print()
    
    # 3. Check WIP item
    print("3. Checking WIP item:")
    wip_item = ItemMaster.query.filter_by(item_code='2015').first()
    if wip_item:
        print(f"   ✓ WIP 2015 exists (ID: {wip_item.id})")
        print(f"     Description: {wip_item.description}")
        print(f"     Item Type: {wip_item.item_type.type_name if wip_item.item_type else 'None'}")
    else:
        print(f"   ✗ WIP 2015 NOT found")
    print()
    
    # 4. Check packing entries
    print("4. Checking packing entries:")
    for fg_code in fg_items:
        fg_item = ItemMaster.query.filter_by(item_code=fg_code).first()
        if fg_item:
            packing_entries = Packing.query.filter_by(item_id=fg_item.id).all()
            if packing_entries:
                for packing in packing_entries:
                    print(f"   FG {fg_code}: {packing.requirement_kg} kg (Week: {packing.week_commencing})")
            else:
                print(f"   FG {fg_code}: No packing entries found")
        print()
    
    # 5. Check filling entries
    print("5. Checking filling entries:")
    for wipf_code in wipf_items:
        wipf_item = ItemMaster.query.filter_by(item_code=wipf_code).first()
        if wipf_item:
            filling_entries = Filling.query.filter_by(item_id=wipf_item.id).all()
            if filling_entries:
                for filling in filling_entries:
                    print(f"   WIPF {wipf_code}: {filling.requirement_kg} kg (Week: {filling.week_commencing})")
            else:
                print(f"   WIPF {wipf_code}: No filling entries found")
        else:
            print(f"   WIPF {wipf_code}: Item doesn't exist, so no filling entries")
        print()
    
    # 6. Check what should happen
    print("6. Analysis - What should happen:")
    fg_2015_100_2 = ItemMaster.query.filter_by(item_code='2015.100.2').first()
    fg_2015_125_02 = ItemMaster.query.filter_by(item_code='2015.125.02').first()
    
    if fg_2015_100_2:
        packing_100_2 = Packing.query.filter_by(item_id=fg_2015_100_2.id).first()
        if packing_100_2:
            print(f"   FG 2015.100.2 has packing requirement: {packing_100_2.requirement_kg} kg")
            if fg_2015_100_2.wipf_item_id:
                print(f"   Should create filling for WIPF ID: {fg_2015_100_2.wipf_item_id}")
                wipf_item = ItemMaster.query.get(fg_2015_100_2.wipf_item_id)
                if wipf_item:
                    print(f"   WIPF Item: {wipf_item.item_code} ({wipf_item.description})")
                else:
                    print(f"   ✗ WIPF Item ID {fg_2015_100_2.wipf_item_id} not found in ItemMaster")
            else:
                print(f"   ✗ FG 2015.100.2 has no WIPF relationship")
        else:
            print(f"   ✗ FG 2015.100.2 has no packing entries")
    
    if fg_2015_125_02:
        packing_125_02 = Packing.query.filter_by(item_id=fg_2015_125_02.id).first()
        if packing_125_02:
            print(f"   FG 2015.125.02 has packing requirement: {packing_125_02.requirement_kg} kg")
            if fg_2015_125_02.wipf_item_id:
                print(f"   Should create filling for WIPF ID: {fg_2015_125_02.wipf_item_id}")
                wipf_item = ItemMaster.query.get(fg_2015_125_02.wipf_item_id)
                if wipf_item:
                    print(f"   WIPF Item: {wipf_item.item_code} ({wipf_item.description})")
                else:
                    print(f"   ✗ WIPF Item ID {fg_2015_125_02.wipf_item_id} not found in ItemMaster")
            else:
                print(f"   ✗ FG 2015.125.02 has no WIPF relationship")
        else:
            print(f"   ✗ FG 2015.125.02 has no packing entries")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        check_2015_relationships() 