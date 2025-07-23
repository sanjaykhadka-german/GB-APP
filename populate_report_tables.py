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

def populate_report_tables_fixed():
    """
    FIXED VERSION: Creates UNIQUE raw material entries per week (aggregated).
    Instead of 718 individual entries, creates ~30-50 unique raw material entries per week.
    
    The issue was that the original script created one entry per production × raw material combination.
    This script creates ONE entry per raw material with aggregated totals across all productions.
    """
    with app.app_context():
        try:
            print("🔧 Starting FIXED report table population...")
            print("This will create UNIQUE entries instead of 718 individual entries!")
            
            # Use specific week
            week_commencing = date(2025, 7, 14)
            print(f"\nProcessing week: {week_commencing}")
            
            # Clear existing data for this week
            print("Clearing existing data...")
            db.session.execute(text("DELETE FROM raw_material_report_table WHERE week_commencing = :week"), {'week': week_commencing})
            db.session.execute(text("DELETE FROM usage_report_table WHERE week_commencing = :week"), {'week': week_commencing})
            db.session.commit()
            
            # 🔧 FIXED APPROACH: Use aggregated query to get totals per raw material per week
            print("Creating aggregated raw material usage data...")
            
            aggregated_query = """
            SELECT 
                component_im.id as raw_material_id,
                component_im.description as raw_material,
                SUM(r.quantity_kg * p.batches) as total_usage_kg,
                COUNT(DISTINCT p.id) as production_count,
                COUNT(DISTINCT production_im.item_code) as recipe_count,
                GROUP_CONCAT(DISTINCT production_im.item_code SEPARATOR ', ') as recipe_codes,
                AVG((r.quantity_kg * p.batches) / p.total_kg * 100) as avg_percentage
            FROM production p
            JOIN item_master production_im ON p.item_id = production_im.id
            JOIN recipe_master r ON production_im.id = r.recipe_wip_id
            JOIN item_master component_im ON r.component_item_id = component_im.id
            JOIN item_type it ON component_im.item_type_id = it.id
            WHERE p.week_commencing = :week_commencing
            AND it.type_name = 'RM'
            GROUP BY component_im.id, component_im.description
            ORDER BY total_usage_kg DESC, component_im.description
            """
            
            results = db.session.execute(
                text(aggregated_query),
                {'week_commencing': week_commencing}
            ).fetchall()
            
            print(f"\n✅ Found {len(results)} unique raw materials with usage (down from 718!)")
            
            if not results:
                print("⚠️  No raw material usage data found for this week.")
                return
            
            # Create ONE entry per raw material with aggregated totals
            for i, result in enumerate(results, 1):
                print(f"\n[{i:2d}/{len(results)}] Processing: {result.raw_material}")
                
                # Insert ONE raw material report entry (aggregated)
                raw_report_sql = """
                INSERT INTO raw_material_report_table 
                (week_commencing, production_date, raw_material_id, raw_material, meat_required, created_at)
                VALUES (:week, :week, :rm_id, :rm_desc, :total_usage, NOW())
                """
                db.session.execute(text(raw_report_sql), {
                    'week': week_commencing,
                    'rm_id': result.raw_material_id,
                    'rm_desc': result.raw_material,
                    'total_usage': float(result.total_usage_kg)
                })
                
                # Insert ONE usage report entry (aggregated)
                # Truncate recipe_codes if too long for database field
                recipe_codes_truncated = result.recipe_codes[:50] if result.recipe_codes else "Multiple"
                
                usage_report_sql = """
                INSERT INTO usage_report_table 
                (week_commencing, production_date, recipe_code, raw_material, usage_kg, percentage, created_at)
                VALUES (:week, :week, :recipe_codes, :rm_desc, :total_usage, :avg_pct, NOW())
                """
                db.session.execute(text(usage_report_sql), {
                    'week': week_commencing,
                    'recipe_codes': recipe_codes_truncated,
                    'rm_desc': result.raw_material,
                    'total_usage': float(result.total_usage_kg),
                    'avg_pct': float(result.avg_percentage) if result.avg_percentage else 0.0
                })
                
                print(f"    ✅ {result.total_usage_kg:.2f} kg total (from {result.production_count} productions, {result.recipe_count} recipes)")
                print(f"       Used in: {result.recipe_codes[:100]}{'...' if len(result.recipe_codes) > 100 else ''}")
            
            # Commit all changes
            db.session.commit()
            print("\n" + "="*60)
            
            # Final verification
            raw_count = db.session.execute(text("SELECT COUNT(*) FROM raw_material_report_table WHERE week_commencing = :week"), {'week': week_commencing}).scalar()
            usage_count = db.session.execute(text("SELECT COUNT(*) FROM usage_report_table WHERE week_commencing = :week"), {'week': week_commencing}).scalar()
            
            print(f"🎉 FIXED Results:")
            print(f"📊 raw_material_report_table: {raw_count} records (down from 718!)")
            print(f"📊 usage_report_table: {usage_count} records (down from 718!)")
            print(f"\n✅ Each raw material now has exactly ONE entry with aggregated totals!")
            print(f"✅ Frontend will now display clean, unique raw material data!")
            print(f"✅ Database is optimized - no more redundant entries!")
            
            # Show top 5 raw materials by usage
            print(f"\n📈 Top 5 Raw Materials by Usage:")
            top_materials_query = """
            SELECT raw_material, meat_required 
            FROM raw_material_report_table 
            WHERE week_commencing = :week 
            ORDER BY meat_required DESC 
            LIMIT 5
            """
            top_materials = db.session.execute(text(top_materials_query), {'week': week_commencing}).fetchall()
            
            for i, material in enumerate(top_materials, 1):
                print(f"  {i}. {material.raw_material}: {material.meat_required:.2f} kg")
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    populate_report_tables_fixed() 