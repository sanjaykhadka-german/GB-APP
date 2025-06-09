from app import app
from models import RawMaterials
from database import db
from sqlalchemy import text

def copy_missing_raw_materials():
    with app.app_context():
        try:
            # Get missing raw materials from recipe_master
            missing_materials = db.session.execute(
                text("""
                    SELECT DISTINCT raw_material 
                    FROM recipe_master 
                    WHERE raw_material_id IS NULL 
                    AND raw_material NOT IN (SELECT raw_material FROM raw_materials)
                    ORDER BY raw_material
                """)
            ).fetchall()
            
            print(f"Found {len(missing_materials)} missing raw materials")
            
            # Insert missing materials into raw_materials table
            for material in missing_materials:
                raw_material = material[0]  # Get the raw_material name from the tuple
                try:
                    result = db.session.execute(
                        text("""
                            INSERT INTO raw_materials (raw_material) 
                            VALUES (:raw_material)
                        """),
                        {"raw_material": raw_material}
                    )
                    print(f"Added '{raw_material}' to raw_materials table")
                except Exception as e:
                    print(f"Error adding '{raw_material}': {str(e)}")
                    continue
            
            db.session.commit()
            
            # Now update recipe_master with new raw_material_ids
            print("\nUpdating recipe_master with new IDs...")
            result = db.session.execute(
                text("""
                    UPDATE recipe_master rm
                    JOIN raw_materials r ON rm.raw_material = r.raw_material
                    SET rm.raw_material_id = r.id
                    WHERE rm.raw_material_id IS NULL
                """)
            )
            
            print(f"Updated {result.rowcount} records in recipe_master")
            db.session.commit()
            
            # Verify the updates
            verification = db.session.execute(
                text("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN raw_material_id IS NOT NULL THEN 1 ELSE 0 END) as with_id,
                        SUM(CASE WHEN raw_material_id IS NULL THEN 1 ELSE 0 END) as without_id
                    FROM recipe_master
                """)
            ).fetchone()
            
            print("\nVerification:")
            print(f"Total records in recipe_master: {verification.total}")
            print(f"Records with raw_material_id: {verification.with_id}")
            print(f"Records without raw_material_id: {verification.without_id}")
            
            # Show sample of new mappings
            print("\nSample of new mappings:")
            new_mappings = db.session.execute(
                text("""
                    SELECT rm.raw_material, rm.raw_material_id, r.raw_material as verified_name
                    FROM recipe_master rm
                    JOIN raw_materials r ON rm.raw_material_id = r.id
                    WHERE rm.raw_material_id > 22
                    LIMIT 5
                """)
            ).fetchall()
            
            for mapping in new_mappings:
                print(f"'{mapping.raw_material}' -> ID: {mapping.raw_material_id}")
            
        except Exception as e:
            print(f"Error during copy: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    copy_missing_raw_materials() 