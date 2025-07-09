from app import app, db
from sqlalchemy import text
from datetime import datetime, timedelta

def fix_report_tables():
    with app.app_context():
        try:
            print("Fixing report tables...")
            
            # Drop existing tables
            db.session.execute(text("DROP TABLE IF EXISTS usage_report_table"))
            db.session.execute(text("DROP TABLE IF EXISTS raw_material_report_table"))
            db.session.commit()
            
            # Create usage_report_table
            create_usage_table_sql = """
            CREATE TABLE usage_report_table (
                id INT AUTO_INCREMENT PRIMARY KEY,
                week_commencing DATE NOT NULL,
                item_id INT NOT NULL,
                monday DECIMAL(10,2) DEFAULT 0.00,
                tuesday DECIMAL(10,2) DEFAULT 0.00,
                wednesday DECIMAL(10,2) DEFAULT 0.00,
                thursday DECIMAL(10,2) DEFAULT 0.00,
                friday DECIMAL(10,2) DEFAULT 0.00,
                total_usage DECIMAL(10,2) DEFAULT 0.00,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES item_master(id)
            )
            """
            db.session.execute(text(create_usage_table_sql))
            
            # Create raw_material_report_table
            create_raw_material_table_sql = """
            CREATE TABLE raw_material_report_table (
                id INT AUTO_INCREMENT PRIMARY KEY,
                week_commencing DATE NOT NULL,
                item_id INT NOT NULL,
                required_total_production DECIMAL(10,2) DEFAULT 0.00,
                value_required_rm DECIMAL(10,2) DEFAULT 0.00,
                current_stock DECIMAL(10,2) DEFAULT 0.00,
                required_for_plan DECIMAL(10,2) DEFAULT 0.00,
                variance_week DECIMAL(10,2) DEFAULT 0.00,
                kg_required DECIMAL(10,2) DEFAULT 0.00,
                variance DECIMAL(10,2) DEFAULT 0.00,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES item_master(id)
            )
            """
            db.session.execute(text(create_raw_material_table_sql))
            
            # Populate usage_report_table from production data
            populate_usage_sql = """
            INSERT INTO usage_report_table (week_commencing, item_id, monday, tuesday, wednesday, thursday, friday, total_usage)
            SELECT 
                p.week_commencing,
                r.component_item_id as item_id,
                SUM(CASE WHEN DAYOFWEEK(p.production_date) = 2 THEN r.quantity_kg * p.batches ELSE 0 END) as monday,
                SUM(CASE WHEN DAYOFWEEK(p.production_date) = 3 THEN r.quantity_kg * p.batches ELSE 0 END) as tuesday,
                SUM(CASE WHEN DAYOFWEEK(p.production_date) = 4 THEN r.quantity_kg * p.batches ELSE 0 END) as wednesday,
                SUM(CASE WHEN DAYOFWEEK(p.production_date) = 5 THEN r.quantity_kg * p.batches ELSE 0 END) as thursday,
                SUM(CASE WHEN DAYOFWEEK(p.production_date) = 6 THEN r.quantity_kg * p.batches ELSE 0 END) as friday,
                SUM(r.quantity_kg * p.batches) as total_usage
            FROM production p
            JOIN recipe_master r ON p.item_id = r.recipe_wip_id
            GROUP BY p.week_commencing, r.component_item_id
            """
            db.session.execute(text(populate_usage_sql))
            
            # Populate raw_material_report_table
            populate_raw_material_sql = """
            INSERT INTO raw_material_report_table (
                week_commencing, item_id, required_total_production, value_required_rm,
                current_stock, required_for_plan, variance_week, kg_required, variance
            )
            SELECT 
                u.week_commencing,
                u.item_id,
                u.total_usage as required_total_production,
                u.total_usage * COALESCE(i.price_per_kg, 0) as value_required_rm,
                COALESCE(s.current_stock, 0) as current_stock,
                u.total_usage as required_for_plan,
                COALESCE(s.current_stock, 0) - u.total_usage as variance_week,
                u.monday as kg_required,
                COALESCE(s.current_stock, 0) - u.monday as variance
            FROM usage_report_table u
            LEFT JOIN item_master i ON u.item_id = i.id
            LEFT JOIN raw_material_stocktake s ON i.item_code = s.item_code AND u.week_commencing = s.week_commencing
            """
            db.session.execute(text(populate_raw_material_sql))
            
            db.session.commit()
            print("Report tables fixed and populated successfully!")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    fix_report_tables() 