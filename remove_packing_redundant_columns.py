from database import db
from sqlalchemy import text
from app import app

def remove_redundant_columns():
    with db.engine.connect() as conn:
        # First update the item_id values where they are missing
        conn.execute(text("""
            UPDATE packing p
            INNER JOIN item_master i ON i.item_code = p.product_code
            SET p.item_id = i.id
            WHERE p.item_id IS NULL
            AND p.product_code IS NOT NULL
        """))
        
        # Verify all records have been updated
        result = conn.execute(text("""
            SELECT COUNT(*) as count
            FROM packing
            WHERE item_id IS NULL
            AND (product_code IS NOT NULL OR product_description IS NOT NULL)
        """))
        count = result.scalar()
        
        if count > 0:
            print(f"WARNING: Found {count} records still missing item_id")
            return
            
        # Drop the foreign key constraint first
        conn.execute(text("""
            ALTER TABLE packing
            DROP FOREIGN KEY fk_packing_soh_week_commencing_product_code
        """))
        
        # Check if index exists before dropping
        result = conn.execute(text("""
            SELECT COUNT(*) as count
            FROM information_schema.statistics
            WHERE table_schema = DATABASE()
            AND table_name = 'packing'
            AND index_name = 'idx_packing_product_code'
        """))
        if result.scalar() > 0:
            conn.execute(text("DROP INDEX idx_packing_product_code ON packing"))
        
        # Drop the redundant columns
        conn.execute(text("""
            ALTER TABLE packing 
            DROP COLUMN product_code,
            DROP COLUMN product_description
        """))
        
        conn.commit()
        print("Successfully removed redundant columns from packing table")

if __name__ == "__main__":
    with app.app_context():
        remove_redundant_columns() 