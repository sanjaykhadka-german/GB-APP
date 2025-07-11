from app import app
from database import db
from models.item_master import ItemMaster
from models.item_type import ItemType
from models.raw_material_report_table import RawMaterialReportTable
from datetime import datetime

def check_raw_material_reports():
    with app.app_context():
        try:
            print("Checking raw material reports in the database...")
            
            # Get total count of reports
            total_reports = RawMaterialReportTable.query.count()
            print(f"\nTotal reports in database: {total_reports}")
            
            # Get all unique weeks
            weeks = db.session.query(RawMaterialReportTable.week_commencing).distinct().all()
            print(f"\nUnique weeks in reports: {len(weeks)}")
            if weeks:
                print("Sample weeks:")
                for week in weeks[:5]:  # Show first 5 weeks
                    print(f"  - {week[0]}")
            
            # Get RM type
            rm_type = ItemType.query.filter_by(type_name='RM').first()
            if not rm_type:
                print("\nError: RM item type not found")
                return
                
            print(f"\nFound RM type with ID: {rm_type.id}")
            
            # Get all raw materials
            raw_materials = ItemMaster.query.filter_by(item_type_id=rm_type.id).all()
            print(f"\nFound {len(raw_materials)} raw materials in ItemMaster")
            
            # Get a sample week
            week_date = datetime.strptime('2025-07-14', '%Y-%m-%d').date()
            
            # Check reports for each raw material
            reports_found = []
            missing_reports = []
            for rm in raw_materials:
                report = RawMaterialReportTable.query.filter_by(
                    item_id=rm.id,
                    week_commencing=week_date
                ).first()
                
                if report:
                    reports_found.append((rm, report))
                else:
                    missing_reports.append(rm)
            
            print(f"\nFor week {week_date}:")
            print(f"Found {len(reports_found)} reports")
            print(f"Missing {len(missing_reports)} reports")
            
            if reports_found:
                print("\nSample reports:")
                for rm, report in reports_found[:5]:  # Show first 5 reports
                    print(f"\n{rm.item_code} - {rm.description}:")
                    print(f"  Required Total: {report.required_total_production}")
                    print(f"  Value Required: {report.value_required_rm}")
                    print(f"  Current Stock: {report.current_stock}")
                    print(f"  Required for Plan: {report.required_for_plan}")
            
            if missing_reports:
                print("\nSample missing reports:")
                for rm in missing_reports[:5]:  # Show first 5 missing reports
                    print(f"  - {rm.item_code}: {rm.description}")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return

if __name__ == '__main__':
    check_raw_material_reports() 