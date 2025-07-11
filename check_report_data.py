from app import app, db
from models.usage_report_table import UsageReportTable
from models.raw_material_report_table import RawMaterialReportTable
from datetime import date
from sqlalchemy import text

def check_report_data():
    with app.app_context():
        try:
            week_commencing = date(2025, 7, 14)
            
            # Check raw counts directly from database
            raw_count_query = "SELECT COUNT(*) as count FROM raw_material_report_table WHERE week_commencing = :week"
            usage_count_query = "SELECT COUNT(*) as count FROM usage_report_table WHERE week_commencing = :week"
            
            raw_count = db.session.execute(text(raw_count_query), {'week': week_commencing}).scalar()
            usage_count = db.session.execute(text(usage_count_query), {'week': week_commencing}).scalar()
            
            print(f"\nDirect database counts:")
            print(f"raw_material_report_table: {raw_count} records")
            print(f"usage_report_table: {usage_count} records")
            
            # Sample data from both tables
            print("\nSampling raw_material_report_table:")
            raw_sample_query = """
            SELECT week_commencing, production_date, raw_material, meat_required 
            FROM raw_material_report_table 
            WHERE week_commencing = :week 
            LIMIT 5
            """
            raw_samples = db.session.execute(text(raw_sample_query), {'week': week_commencing}).fetchall()
            for row in raw_samples:
                print(f"  {row.raw_material}: {row.meat_required} kg on {row.production_date}")
            
            print("\nSampling usage_report_table:")
            usage_sample_query = """
            SELECT week_commencing, production_date, recipe_code, raw_material, usage_kg, percentage 
            FROM usage_report_table 
            WHERE week_commencing = :week 
            LIMIT 5
            """
            usage_samples = db.session.execute(text(usage_sample_query), {'week': week_commencing}).fetchall()
            for row in usage_samples:
                print(f"  {row.raw_material} in {row.recipe_code}: {row.usage_kg} kg ({row.percentage}%)")

        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == '__main__':
    check_report_data() 