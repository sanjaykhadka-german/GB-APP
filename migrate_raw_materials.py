from app import app
from models import RecipeMaster, RawMaterials
from database import db
from sqlalchemy import text

def migrate_raw_materials():
    with app.app_context():
        try:
            # Get all unique raw materials from raw_material table
            result = db.session.execute(text("SELECT DISTINCT raw_material FROM raw_material WHERE raw_material IS NOT NULL"))
            raw_materials = [row[0] for row in result]
            print(f"Found {len(raw_materials)} unique raw materials")
            
            # Insert into raw_materials table
            added_count = 0
            for raw_material in raw_materials:
                if raw_material:
                    existing = RawMaterials.query.filter_by(raw_material=raw_material).first()
                    if not existing:
                        new_raw_material = RawMaterials(raw_material=raw_material)
                        db.session.add(new_raw_material)
                        added_count += 1
            
            print(f"Adding {added_count} new raw materials")
            db.session.commit()
            
            print("Migration completed successfully!")
            print(f"Summary:")
            print(f"- {len(raw_materials)} unique raw materials found")
            print(f"- {added_count} new raw materials added")
            
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    migrate_raw_materials() 