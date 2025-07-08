from app import create_app, db
from models.packing import Packing
from models.filling import Filling
from models.production import Production
from models.usage_report_table import UsageReportTable
from models.raw_material_report_table import RawMaterialReportTable
from models.recipe_master import RecipeMaster
from models.item_master import ItemMaster
from models.item_type import ItemType
from datetime import datetime

def check_downstream():
    """Check downstream entries for each packing entry"""
    # Get all packing entries
    packing_entries = Packing.query.all()
    print(f"\nFound {len(packing_entries)} packing entries")
    
    for packing in packing_entries:
        print(f"\nPacking Entry {packing.id}:")
        print(f"- FG Code: {packing.item.item_code if packing.item else 'No item'}")
        print(f"- Week Commencing: {packing.week_commencing}")
        print(f"- Requirement KG: {packing.requirement_kg}")
        
        if packing.item:
            # Check filling entry
            if packing.item.wipf_item_id:
                filling = Filling.query.filter_by(
                    item_id=packing.item.wipf_item_id,
                    week_commencing=packing.week_commencing
                ).first()
                print("\nFilling Entry:")
                print(f"- Exists: {bool(filling)}")
                if filling:
                    print(f"- Item: {filling.item.item_code}")
                    print(f"- Requirement KG: {filling.requirement_kg}")
            
            # Check production entry
            if packing.item.wip_item_id:
                production = Production.query.filter_by(
                    item_id=packing.item.wip_item_id,
                    week_commencing=packing.week_commencing
                ).first()
                print("\nProduction Entry:")
                print(f"- Exists: {bool(production)}")
                if production:
                    print(f"- Item: {production.item.item_code}")
                    print(f"- Requirement KG: {production.requirement_kg}")
                    
                    # Check usage reports
                    usage_reports = UsageReportTable.query.filter_by(
                        week_commencing=packing.week_commencing,
                        recipe_code=packing.item.wip_item.item_code
                    ).all()
                    print(f"\nUsage Reports ({len(usage_reports)}):")
                    for report in usage_reports:
                        print(f"- Raw Material: {report.raw_material}")
                        print(f"  Usage KG: {report.usage_kg}")
                        print(f"  Percentage: {report.percentage}%")
                    
                    # Check raw material reports
                    raw_reports = RawMaterialReportTable.query.filter_by(
                        week_commencing=packing.week_commencing
                    ).all()
                    print(f"\nRaw Material Reports ({len(raw_reports)}):")
                    for report in raw_reports:
                        print(f"- Raw Material: {report.raw_material}")
                        print(f"  Required KG: {report.meat_required}")

def check_missing_wipf():
    missing_wipf = db.session.query(ItemMaster).join(ItemType).filter(
        ItemMaster.item_code.in_(['2015.100', '2015.125']),
        ItemType.type_name == 'WIPF'
    ).all()
    
    if not missing_wipf:
        print("WIPF items 2015.100 and 2015.125 are missing")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        check_downstream() 