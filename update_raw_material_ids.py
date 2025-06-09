from app import app
from models import RawMaterials, RawMaterialReport
from database import db
from sqlalchemy import text

def update_raw_material_ids():
    with app.app_context():
        try:
            # Get the mapping of raw materials to their IDs
            raw_materials_dict = {rm.raw_material: rm.id for rm in RawMaterials.query.all()}
            print(f"Found {len(raw_materials_dict)} raw materials for mapping")
            
            # Update raw_material_report using raw SQL for better performance
            update_count = 0
            for raw_material, raw_material_id in raw_materials_dict.items():
                result = db.session.execute(
                    text("""
                        UPDATE raw_material_report 
                        SET raw_material_id = :id 
                        WHERE raw_material = :raw_material
                    """),
                    {"id": raw_material_id, "raw_material": raw_material}
                )
                update_count += result.rowcount
            
            db.session.commit()
            
            print("Update completed successfully!")
            print(f"Summary:")
            print(f"- {update_count} records updated with raw_material_id")
            
        except Exception as e:
            print(f"Error during update: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    update_raw_material_ids() 