from app import app, db
from models.item_master import ItemMaster
from models.item_type import ItemType
from models.production import Production
from models.recipe_master import RecipeMaster
from models.usage_report_table import UsageReportTable
from models.raw_material_report_table import RawMaterialReportTable
from sqlalchemy import func, text
from datetime import datetime, timedelta, date
from decimal import Decimal

def populate_report_tables():
    with app.app_context():
        try:
            print("Starting report table population...")
            
            # Get raw material type
            rm_type = ItemType.query.filter_by(type_name='RM').first()
            if not rm_type:
                print("Error: Raw Material type not found")
                return
            
            # Get all raw materials
            raw_materials = ItemMaster.query.filter_by(item_type_id=rm_type.id).all()
            print(f"\nFound {len(raw_materials)} raw materials")
            
            # Use specific week
            week_commencing = date(2025, 7, 14)
            print(f"\nProcessing week: {week_commencing}")
            
            # Clear existing data for this week using raw SQL to ensure deletion
            db.session.execute(text("DELETE FROM raw_material_report_table WHERE week_commencing = :week"), {'week': week_commencing})
            db.session.execute(text("DELETE FROM usage_report_table WHERE week_commencing = :week"), {'week': week_commencing})
            db.session.commit()
            
            # Process each raw material
            for raw_material in raw_materials:
                try:
                    print(f"\nProcessing {raw_material.description}")
                    
                    # Get usage from recipe_master and production
                    usage_query = """
                    SELECT 
                        p.production_date,
                        p.item_id as recipe_id,
                        i.item_code as recipe_code,
                        i.description as recipe_name,
                        r.quantity_kg as usage_per_batch,
                        p.batches,
                        p.total_kg as total_production,
                        (r.quantity_kg * p.batches) as total_usage,
                        ((r.quantity_kg * p.batches) / p.total_kg * 100) as percentage
                    FROM production p
                    JOIN recipe_master r ON p.item_id = r.recipe_wip_id
                    JOIN item_master i ON p.item_id = i.id
                    WHERE r.component_item_id = :item_id
                    AND p.week_commencing = :week_commencing
                    """
                    
                    results = db.session.execute(
                        text(usage_query),
                        {'item_id': raw_material.id, 'week_commencing': week_commencing}
                    ).fetchall()
                    
                    # Process each production record
                    total_usage = Decimal('0')
                    for result in results:
                        usage = Decimal(str(result.total_usage)) if result.total_usage else Decimal('0')
                        total_usage += usage
                        
                        # Insert raw material report using raw SQL
                        raw_report_sql = """
                        INSERT INTO raw_material_report_table 
                        (week_commencing, production_date, raw_material_id, raw_material, meat_required, created_at)
                        VALUES (:week, :prod_date, :rm_id, :rm_desc, :meat_req, NOW())
                        """
                        db.session.execute(text(raw_report_sql), {
                            'week': week_commencing,
                            'prod_date': result.production_date,
                            'rm_id': raw_material.id,
                            'rm_desc': raw_material.description,
                            'meat_req': float(usage)
                        })
                        
                        # Insert usage report using raw SQL
                        usage_report_sql = """
                        INSERT INTO usage_report_table 
                        (week_commencing, production_date, recipe_code, raw_material, usage_kg, percentage, created_at)
                        VALUES (:week, :prod_date, :recipe_code, :rm_desc, :usage, :pct, NOW())
                        """
                        db.session.execute(text(usage_report_sql), {
                            'week': week_commencing,
                            'prod_date': result.production_date,
                            'recipe_code': result.recipe_code,
                            'rm_desc': raw_material.description,
                            'usage': float(usage),
                            'pct': float(result.percentage) if result.percentage else 0.0
                        })
                        
                        print(f"  - Date: {result.production_date}, Recipe: {result.recipe_code}, Usage: {usage:.2f} kg, Percentage: {result.percentage:.2f}%")
                    
                    # Commit after each raw material to ensure data is saved
                    db.session.commit()
                    print(f"Added reports for {raw_material.description}: Total usage {total_usage:.2f} kg")
                    
                except Exception as e:
                    print(f"Error processing {raw_material.description}: {str(e)}")
                    db.session.rollback()
                    continue
            
            # Final verification
            raw_count = db.session.execute(text("SELECT COUNT(*) FROM raw_material_report_table WHERE week_commencing = :week"), {'week': week_commencing}).scalar()
            usage_count = db.session.execute(text("SELECT COUNT(*) FROM usage_report_table WHERE week_commencing = :week"), {'week': week_commencing}).scalar()
            print(f"\nVerification counts:")
            print(f"raw_material_report_table: {raw_count} records")
            print(f"usage_report_table: {usage_count} records")
            
            print("\nReport tables populated successfully!")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    populate_report_tables() 