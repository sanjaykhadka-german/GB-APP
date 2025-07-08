from app import create_app, db
from models.packing import Packing
from models.filling import Filling
from models.production import Production
from models.usage_report_table import UsageReportTable
from models.raw_material_report_table import RawMaterialReportTable
from models.item_master import ItemMaster
from controllers.recipe_controller import usage, raw_material_report
from sqlalchemy import func

def check_aggregation_issues():
    """Check if aggregation issues are fixed"""
    print("Checking aggregation issues...\n")
    
    # 1. Check packing vs production totals
    print("1. Checking packing vs production totals:")
    packing_total = db.session.query(func.sum(Packing.requirement_kg)).scalar() or 0
    production_total = db.session.query(func.sum(Production.total_kg)).scalar() or 0
    
    print(f"   Packing total: {packing_total:.2f} kg")
    print(f"   Production total: {production_total:.2f} kg")
    print(f"   Difference: {abs(packing_total - production_total):.2f} kg")
    
    if abs(packing_total - production_total) < 0.01:
        print("   ✓ Totals match!")
    else:
        print("   ✗ Totals don't match")
    
    # 2. Check WIP aggregation (1004 and 2015)
    print("\n2. Checking WIP aggregation:")
    
    # Check 1004 items
    fg_1004_items = ItemMaster.query.filter(
        ItemMaster.item_code.in_(['1004.090.1', '1004.200.1'])
    ).all()
    
    if fg_1004_items:
        total_1004_packing = 0
        for fg in fg_1004_items:
            fg_packing = db.session.query(func.sum(Packing.requirement_kg)).filter_by(item_id=fg.id).scalar() or 0
            total_1004_packing += fg_packing
            print(f"   FG {fg.item_code}: {fg_packing:.2f} kg")
        
        # Check production for WIP 1004
        wip_1004 = ItemMaster.query.filter_by(item_code='1004').first()
        if wip_1004:
            wip_1004_production = db.session.query(func.sum(Production.total_kg)).filter_by(item_id=wip_1004.id).scalar() or 0
            print(f"   WIP 1004 production: {wip_1004_production:.2f} kg")
            
            if abs(total_1004_packing - wip_1004_production) < 0.01:
                print("   ✓ 1004 aggregation correct!")
            else:
                print("   ✗ 1004 aggregation incorrect")
    
    # Check 2015 items
    fg_2015_items = ItemMaster.query.filter(
        ItemMaster.item_code.in_(['2015.125.02', '2015.100.2'])
    ).all()
    
    if fg_2015_items:
        total_2015_packing = 0
        for fg in fg_2015_items:
            fg_packing = db.session.query(func.sum(Packing.requirement_kg)).filter_by(item_id=fg.id).scalar() or 0
            total_2015_packing += fg_packing
            print(f"   FG {fg.item_code}: {fg_packing:.2f} kg")
        
        # Check production for WIP 2015
        wip_2015 = ItemMaster.query.filter_by(item_code='2015').first()
        if wip_2015:
            wip_2015_production = db.session.query(func.sum(Production.total_kg)).filter_by(item_id=wip_2015.id).scalar() or 0
            print(f"   WIP 2015 production: {wip_2015_production:.2f} kg")
            
            if abs(total_2015_packing - wip_2015_production) < 0.01:
                print("   ✓ 2015 aggregation correct!")
            else:
                print("   ✗ 2015 aggregation incorrect")
    
    # 3. Check WIPF aggregation (1004.6500)
    print("\n3. Checking WIPF aggregation:")
    
    # Check if 1004.6500 exists in filling
    wipf_1004 = ItemMaster.query.filter_by(item_code='1004.6500').first()
    if wipf_1004:
        wipf_1004_filling = db.session.query(func.sum(Filling.requirement_kg)).filter_by(item_id=wipf_1004.id).scalar() or 0
        print(f"   WIPF 1004.6500 filling: {wipf_1004_filling:.2f} kg")
        
        if wipf_1004_filling > 0:
            print("   ✓ WIPF 1004.6500 has filling entries")
        else:
            print("   ✗ WIPF 1004.6500 has no filling entries")
    
    # Check if missing WIPF items exist
    missing_wipf = ['2015.100', '2015.125']
    for wipf_code in missing_wipf:
        wipf_item = ItemMaster.query.filter_by(item_code=wipf_code).first()
        if wipf_item:
            wipf_filling = db.session.query(func.sum(Filling.requirement_kg)).filter_by(item_id=wipf_item.id).scalar() or 0
            print(f"   WIPF {wipf_code} filling: {wipf_filling:.2f} kg")
        else:
            print(f"   ✗ WIPF {wipf_code} does not exist")
    
    # 4. Check usage reports have proper data
    print("\n4. Checking usage reports:")
    usage_count = UsageReportTable.query.count()
    unknown_recipes = UsageReportTable.query.filter_by(recipe_code='Unknown').count()
    zero_usage = UsageReportTable.query.filter_by(usage_kg=0).count()
    
    print(f"   Total usage reports: {usage_count}")
    print(f"   Unknown recipe codes: {unknown_recipes}")
    print(f"   Zero usage entries: {zero_usage}")
    
    if usage_count > 0 and unknown_recipes == 0 and zero_usage == 0:
        print("   ✓ Usage reports look good!")
    else:
        print("   ✗ Usage reports have issues")
    
    # 5. Check raw material reports
    print("\n5. Checking raw material reports:")
    raw_count = RawMaterialReportTable.query.count()
    zero_meat = RawMaterialReportTable.query.filter_by(meat_required=0).count()
    
    print(f"   Total raw material reports: {raw_count}")
    print(f"   Zero meat required entries: {zero_meat}")
    
    if raw_count > 0 and zero_meat == 0:
        print("   ✓ Raw material reports look good!")
    else:
        print("   ✗ Raw material reports have issues")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        check_aggregation_issues() 