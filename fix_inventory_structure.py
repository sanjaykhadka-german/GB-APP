from app import app, db
from sqlalchemy import text

def fix_inventory_structure():
    with app.app_context():
        try:
            print("Fixing inventory table structure...")
            
            # Drop existing inventory table
            db.session.execute(text("DROP TABLE IF EXISTS inventory"))
            db.session.commit()
            
            # Create new inventory table with correct structure
            create_table_sql = """
            CREATE TABLE inventory (
                id INT AUTO_INCREMENT PRIMARY KEY,
                week_commencing DATE NOT NULL,
                item_id INT NOT NULL,
                category_id INT NOT NULL,
                price_per_kg DECIMAL(10,2) DEFAULT 0.00,
                required_total_production DECIMAL(10,2) DEFAULT 0.00,
                value_required_rm DECIMAL(10,2) DEFAULT 0.00,
                current_stock DECIMAL(10,2) DEFAULT 0.00,
                supplier_name VARCHAR(255),
                required_for_plan DECIMAL(10,2) DEFAULT 0.00,
                variance_week DECIMAL(10,2) DEFAULT 0.00,
                kg_required DECIMAL(10,2) DEFAULT 0.00,
                variance DECIMAL(10,2) DEFAULT 0.00,
                to_be_ordered DECIMAL(10,2) DEFAULT 0.00,
                closing_stock DECIMAL(10,2) DEFAULT 0.00,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES item_master(id),
                FOREIGN KEY (category_id) REFERENCES category(id)
            )
            """
            db.session.execute(text(create_table_sql))
            db.session.commit()
            
            print("Inventory table structure updated successfully!")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    fix_inventory_structure() 