from database import db
from sqlalchemy import text
from app import app

def verify_packing_data():
    with db.engine.connect() as conn:
        # Check for foreign key constraints
        result = conn.execute(text("""
            SELECT 
                CONSTRAINT_NAME,
                TABLE_NAME,
                COLUMN_NAME,
                REFERENCED_TABLE_NAME,
                REFERENCED_COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE REFERENCED_TABLE_SCHEMA = DATABASE()
            AND (TABLE_NAME = 'packing' OR REFERENCED_TABLE_NAME = 'packing')
            AND CONSTRAINT_NAME LIKE 'fk%'
        """))
        constraints = result.fetchall()
        
        print("Foreign Key Constraints:")
        print("-" * 80)
        for constraint in constraints:
            print(f"Constraint: {constraint.CONSTRAINT_NAME}")
            print(f"Table: {constraint.TABLE_NAME}.{constraint.COLUMN_NAME}")
            print(f"References: {constraint.REFERENCED_TABLE_NAME}.{constraint.REFERENCED_COLUMN_NAME}")
            print("-" * 80)
            
        # Check if columns exist
        result = conn.execute(text("""
            SELECT COUNT(*) as count 
            FROM information_schema.columns 
            WHERE table_name = 'packing' 
            AND column_name IN ('product_code', 'product_description')
        """))
        count = result.scalar()
        
        if count == 0:
            print("Columns product_code and product_description have already been removed")
            return
            
        # Check for any records with non-null values in these columns
        result = conn.execute(text("""
            SELECT COUNT(*) as count 
            FROM packing 
            WHERE product_code IS NOT NULL 
            OR product_description IS NOT NULL
        """))
        records_count = result.scalar()
        print(f"\nFound {records_count} packing records with product code or description")
        
        if records_count > 0:
            # Show details of records without item_id
            result = conn.execute(text("""
                SELECT p.id, p.product_code, p.product_description, p.packing_date,
                       i.id as item_id, i.item_code
                FROM packing p
                LEFT JOIN item_master i ON i.item_code = p.product_code
                WHERE (p.product_code IS NOT NULL OR p.product_description IS NOT NULL)
                AND p.item_id IS NULL
            """))
            rows = result.fetchall()
            if rows:
                print(f"\nFound {len(rows)} records with missing item_id:")
                print("\nPacking ID | Product Code | Description | Matching Item ID")
                print("-" * 70)
                for row in rows:
                    print(f"{row.id} | {row.product_code or 'None'} | {row.product_description or 'None'} | {row.item_id or 'No match'}")

if __name__ == "__main__":
    with app.app_context():
        verify_packing_data() 