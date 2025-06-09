from app import app
from models import RawMaterials
from database import db
from sqlalchemy import text

def revert_recipe_master():
    with app.app_context():
        try:
            # First, check if raw_material column exists
            has_column = db.session.execute(
                text("""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = 'gbdb' 
                    AND TABLE_NAME = 'recipe_master' 
                    AND COLUMN_NAME = 'raw_material'
                """)
            ).scalar()

            # Add raw_material column if it doesn't exist
            if not has_column:
                print("Adding raw_material column to recipe_master...")
                db.session.execute(
                    text("""
                        ALTER TABLE recipe_master 
                        ADD COLUMN raw_material VARCHAR(255) NULL 
                        AFTER description
                    """)
                )
                db.session.commit()

            # Update raw_material values from raw_materials table
            print("\nUpdating raw_material values in recipe_master...")
            result = db.session.execute(
                text("""
                    UPDATE recipe_master rm
                    JOIN raw_materials r ON rm.raw_material_id = r.id
                    SET rm.raw_material = r.raw_material
                """)
            )
            
            print(f"Updated {result.rowcount} records in recipe_master")
            db.session.commit()

            # Verify the update
            verification = db.session.execute(
                text("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN raw_material IS NOT NULL THEN 1 ELSE 0 END) as with_raw_material,
                        SUM(CASE WHEN raw_material_id IS NOT NULL THEN 1 ELSE 0 END) as with_raw_material_id
                    FROM recipe_master
                """)
            ).fetchone()
            
            total, with_raw_material, with_raw_material_id = verification
            print("\nVerification:")
            print(f"Total records: {total}")
            print(f"Records with raw_material: {with_raw_material}")
            print(f"Records with raw_material_id: {with_raw_material_id}")

        except Exception as e:
            print(f"Error during revert: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    revert_recipe_master() 