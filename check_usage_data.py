from flask import Flask
from database import db
from sqlalchemy.sql import text
from models import Production, RecipeMaster, RawMaterials, UsageReport
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', 'mysql://admin:admin@localhost/gb_app')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def check_usage_data():
    with app.app_context():
        try:
            # Check if usage_report table exists
            check_table_query = text("""
                SELECT COUNT(*) as table_exists 
                FROM information_schema.tables 
                WHERE table_schema = 'gbdb' 
                AND table_name = 'usage_report'
            """)
            result = db.session.execute(check_table_query).fetchone()
            print(f"\nUsage Report table exists: {result.table_exists > 0}")

            if result.table_exists > 0:
                # Check table structure
                structure_query = text("""
                    DESCRIBE usage_report
                """)
                columns = db.session.execute(structure_query).fetchall()
                print("\nTable structure:")
                for col in columns:
                    print(f"- {col.Field}: {col.Type}")

                # Count records
                count_query = text("""
                    SELECT COUNT(*) as record_count 
                    FROM usage_report
                """)
                count = db.session.execute(count_query).fetchone()
                print(f"\nTotal records: {count.record_count}")

                if count.record_count > 0:
                    # Sample some records
                    sample_query = text("""
                        SELECT * FROM usage_report 
                        ORDER BY production_date DESC 
                        LIMIT 5
                    """)
                    samples = db.session.execute(sample_query).fetchall()
                    print("\nSample records:")
                    for record in samples:
                        print(f"Date: {record.production_date}")
                        print(f"Recipe: {record.recipe_code}")
                        print(f"Material: {record.raw_material}")
                        print(f"Usage: {record.usage_kg} kg")
                        print(f"Percentage: {record.percentage}%")
                        print()

            # Check production data
            prod_query = text("""
                SELECT 
                    p.production_date,
                    p.production_code,
                    p.total_kg,
                    COUNT(DISTINCT r.id) as recipe_count,
                    GROUP_CONCAT(DISTINCT rm.raw_material) as materials
                FROM production p
                JOIN recipe_master r ON p.production_code = r.recipe_code
                JOIN raw_materials rm ON r.raw_material_id = rm.id
                GROUP BY p.production_date, p.production_code, p.total_kg
            """)
            productions = db.session.execute(prod_query).fetchall()
            print("\nProduction data:")
            for prod in productions:
                print(f"Date: {prod.production_date}")
                print(f"Code: {prod.production_code}")
                print(f"Total KG: {prod.total_kg}")
                print(f"Recipe Count: {prod.recipe_count}")
                print(f"Materials: {prod.materials}")
                print()

        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == '__main__':
    check_usage_data() 