from app import app
from models import RawMaterials
from database import db
from sqlalchemy import text

def update_recipe_master_ids():
    with app.app_context():
        try:
            # Get all raw materials and their IDs
            raw_materials = db.session.execute(
                text("SELECT id, raw_material FROM raw_materials")
            ).fetchall()
            
            raw_material_map = {rm.raw_material: rm.id for rm in raw_materials}
            print(f"Found {len(raw_material_map)} raw materials")
            
            # Update recipe_master records
            total_updates = 0
            for raw_material, raw_material_id in raw_material_map.items():
                result = db.session.execute(
                    text("""
                        UPDATE recipe_master 
                        SET raw_material_id = :id 
                        WHERE raw_material = :raw_material
                    """),
                    {"id": raw_material_id, "raw_material": raw_material}
                )
                if result.rowcount > 0:
                    print(f"Updated {result.rowcount} records for '{raw_material}' (ID: {raw_material_id})")
                    total_updates += result.rowcount
            
            db.session.commit()
            print(f"\nTotal records updated: {total_updates}")
            
            # Verify updates
            verification = db.session.execute(
                text("""
                    SELECT rm.recipe_code, rm.raw_material, rm.kg_per_batch, 
                           rm.raw_material_id, r.raw_material as raw_material_name
                    FROM recipe_master rm
                    JOIN raw_materials r ON rm.raw_material_id = r.id
                    LIMIT 5
                """)
            ).fetchall()
            
            print("\nSample of updated records:")
            print("Recipe Code | Raw Material | KG per Batch | Raw Material ID | Raw Material Name")
            print("-" * 75)
            for row in verification:
                print(f"{row.recipe_code:11} | {row.raw_material:12} | {row.kg_per_batch:11} | {row.raw_material_id:14} | {row.raw_material_name}")
            
            # Check for any unmatched records
            unmatched = db.session.execute(
                text("""
                    SELECT raw_material, COUNT(*) as count
                    FROM recipe_master
                    WHERE raw_material_id IS NULL
                    GROUP BY raw_material
                """)
            ).fetchall()
            
            if unmatched:
                print("\nWarning: Found unmatched raw materials:")
                for row in unmatched:
                    print(f"- {row.raw_material}: {row.count} records")
            
        except Exception as e:
            print(f"Error during update: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    update_recipe_master_ids() 