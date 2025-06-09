from app import app
from models import RawMaterials
from database import db
from sqlalchemy import text

def update_raw_material_refs():
    with app.app_context():
        try:
            # Get the mapping of raw materials to their IDs
            raw_materials_dict = {rm.raw_material: rm.id for rm in RawMaterials.query.all()}
            print(f"Found {len(raw_materials_dict)} raw materials for mapping")
            
            total_updates = 0
            
            # Update raw_material_report
            print("\nUpdating raw_material_report...")
            for raw_material, raw_material_id in raw_materials_dict.items():
                result = db.session.execute(
                    text("""
                        UPDATE raw_material_report 
                        SET raw_material_id = :id 
                        WHERE raw_material = :raw_material
                    """),
                    {"id": raw_material_id, "raw_material": raw_material}
                )
                if result.rowcount > 0:
                    print(f"- Updated {result.rowcount} records for '{raw_material}'")
                    total_updates += result.rowcount
            db.session.commit()

            # Update usage_report
            print("\nUpdating usage_report...")
            for raw_material, raw_material_id in raw_materials_dict.items():
                result = db.session.execute(
                    text("""
                        UPDATE usage_report 
                        SET raw_material_id = :id 
                        WHERE raw_material = :raw_material
                    """),
                    {"id": raw_material_id, "raw_material": raw_material}
                )
                if result.rowcount > 0:
                    print(f"- Updated {result.rowcount} records for '{raw_material}'")
                    total_updates += result.rowcount
            db.session.commit()

            # Update recipe_master
            print("\nUpdating recipe_master...")
            for raw_material, raw_material_id in raw_materials_dict.items():
                result = db.session.execute(
                    text("""
                        UPDATE recipe_master 
                        SET raw_material_id = :id 
                        WHERE raw_material_id IS NULL
                        AND EXISTS (
                            SELECT 1 FROM raw_material_report 
                            WHERE raw_material = :raw_material 
                            AND raw_material_id = :id
                        )
                    """),
                    {"id": raw_material_id, "raw_material": raw_material}
                )
                if result.rowcount > 0:
                    print(f"- Updated {result.rowcount} records for '{raw_material}'")
                    total_updates += result.rowcount
            db.session.commit()

            # Update usage table
            print("\nUpdating usage table...")
            for raw_material, raw_material_id in raw_materials_dict.items():
                result = db.session.execute(
                    text("""
                        UPDATE `usage` 
                        SET raw_material_id = :id 
                        WHERE raw_material_id IS NULL
                        AND EXISTS (
                            SELECT 1 FROM usage_report 
                            WHERE raw_material = :raw_material 
                            AND raw_material_id = :id
                        )
                    """),
                    {"id": raw_material_id, "raw_material": raw_material}
                )
                if result.rowcount > 0:
                    print(f"- Updated {result.rowcount} records for '{raw_material}'")
                    total_updates += result.rowcount
            db.session.commit()
            
            print("\nUpdate completed successfully!")
            print(f"Summary:")
            print(f"- {len(raw_materials_dict)} raw materials found")
            print(f"- {total_updates} total records updated across all tables")
            
            # Print verification queries
            print("\nVerification:")
            tables = ['raw_material_report', 'usage_report', 'recipe_master', '`usage`']
            for table in tables:
                result = db.session.execute(
                    text(f"""
                        SELECT COUNT(*) as total, 
                               SUM(CASE WHEN raw_material_id IS NOT NULL THEN 1 ELSE 0 END) as with_id
                        FROM {table}
                    """)
                ).fetchone()
                total, with_id = result
                print(f"{table}: {with_id}/{total} records have raw_material_id")
            
        except Exception as e:
            print(f"Error during update: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    update_raw_material_refs() 