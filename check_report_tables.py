from app import app
from database import db
from models.raw_material_report_table import RawMaterialReportTable
from models.usage_report_table import UsageReportTable

def check_report_tables():
    with app.app_context():
        raw_material_count = RawMaterialReportTable.query.count()
        usage_count = UsageReportTable.query.count()
        
        print(f"\nRaw Material Reports: {raw_material_count}")
        print(f"Usage Reports: {usage_count}")
        
        if raw_material_count > 0:
            sample = RawMaterialReportTable.query.first()
            print("\nSample Raw Material Report:")
            print(f"Week: {sample.week_commencing}")
            print(f"Item: {sample.item.description if sample.item else 'N/A'}")
            print(f"Required Total Production: {sample.required_total_production}")
            print(f"Value Required RM: {sample.value_required_rm}")
            print(f"Current Stock: {sample.current_stock}")
            print(f"Required for Plan: {sample.required_for_plan}")
            print(f"Variance Week: {sample.variance_week}")
            print(f"KG Required: {sample.kg_required}")
            print(f"Variance: {sample.variance}")
        
        if usage_count > 0:
            sample = UsageReportTable.query.first()
            print("\nSample Usage Report:")
            print(f"Week: {sample.week_commencing}")
            print(f"Item: {sample.item.description if sample.item else 'N/A'}")
            print(f"Monday: {sample.monday}")
            print(f"Tuesday: {sample.tuesday}")
            print(f"Wednesday: {sample.wednesday}")
            print(f"Thursday: {sample.thursday}")
            print(f"Friday: {sample.friday}")
            print(f"Total Usage: {sample.total_usage}")

if __name__ == '__main__':
    check_report_tables() 