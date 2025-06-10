from flask import Flask
from database import db
from sqlalchemy.sql import text
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:german@localhost/gbdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def update_usage_report():
    with app.app_context():
        try:
            # First, clear the existing data
            clear_query = text("TRUNCATE TABLE usage_report")
            db.session.execute(clear_query)
            
            # Create a temporary table for recipe totals
            create_temp_query = text("""
                CREATE TEMPORARY TABLE recipe_total_kg AS
                SELECT 
                    recipe_code,
                    SUM(kg_per_batch) as total_recipe_kg
                FROM recipe_master
                GROUP BY recipe_code
            """)
            db.session.execute(create_temp_query)
            
            # Calculate and insert new usage data
            usage_query = text("""
                INSERT INTO usage_report (
                    week_commencing,
                    production_date,
                    recipe_code,
                    raw_material,
                    usage_kg,
                    percentage,
                    created_at
                )
                SELECT 
                    DATE_SUB(p.production_date, INTERVAL WEEKDAY(p.production_date) DAY) as week_commencing,
                    p.production_date,
                    p.production_code as recipe_code,
                    rm.raw_material,
                    (p.total_kg * r.kg_per_batch / rt.total_recipe_kg) as usage_kg,
                    (r.kg_per_batch / rt.total_recipe_kg * 100) as percentage,
                    NOW() as created_at
                FROM production p
                JOIN recipe_master r ON p.production_code = r.recipe_code
                JOIN recipe_total_kg rt ON r.recipe_code = rt.recipe_code
                JOIN raw_materials rm ON r.raw_material_id = rm.id
                WHERE p.total_kg > 0
                ORDER BY p.production_date DESC, p.production_code, rm.raw_material
            """)
            
            print("Updating usage report data...")
            db.session.execute(usage_query)
            db.session.commit()
            print("Usage report data updated successfully!")
            
            # Drop the temporary table
            drop_temp_query = text("DROP TEMPORARY TABLE IF EXISTS recipe_total_kg")
            db.session.execute(drop_temp_query)
            
            # Verify the data
            verify_query = text("SELECT COUNT(*) as count FROM usage_report")
            result = db.session.execute(verify_query).fetchone()
            print(f"Total records in usage_report: {result.count}")
            
            # Show some sample records
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
                
        except Exception as e:
            print(f"Error: {str(e)}")
            db.session.rollback()
            
            # Make sure to drop the temporary table in case of error
            try:
                drop_temp_query = text("DROP TEMPORARY TABLE IF EXISTS recipe_total_kg")
                db.session.execute(drop_temp_query)
            except:
                pass

if __name__ == '__main__':
    update_usage_report() 