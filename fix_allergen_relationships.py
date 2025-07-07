from app import app
from database import db
from models.item_master import ItemMaster, ItemAllergen
from models.allergen import Allergen
from sqlalchemy import text

def fix_allergen_relationships():
    with app.app_context():
        # Get all items with allergens
        result = db.session.execute(text("""
            SELECT DISTINCT item_id, allergen_id
            FROM item_allergen
            ORDER BY item_id, allergen_id
        """))
        
        # Group allergens by item
        item_allergens = {}
        for row in result:
            if row.item_id not in item_allergens:
                item_allergens[row.item_id] = []
            item_allergens[row.item_id].append(row.allergen_id)
        
        # Process each item
        for item_id, allergen_ids in item_allergens.items():
            print(f"\nProcessing item ID {item_id}:")
            print(f"Found allergen IDs in junction table: {allergen_ids}")
            
            # Get the item
            item = ItemMaster.query.get(item_id)
            if not item:
                print(f"Warning: Item {item_id} not found in database")
                continue
            
            print(f"Item code: {item.item_code}")
            print(f"Current allergens: {[f'{a.name} (ID: {a.allergens_id})' for a in item.allergens]}")
            
            # Get the allergens
            allergens = Allergen.query.filter(Allergen.allergens_id.in_(allergen_ids)).all()
            found_ids = {a.allergens_id for a in allergens}
            missing_ids = set(allergen_ids) - found_ids
            
            if missing_ids:
                print(f"Warning: Could not find allergens with IDs: {missing_ids}")
            
            # Update the relationship
            item.allergens = allergens
            print(f"Updated allergens to: {[f'{a.name} (ID: {a.allergens_id})' for a in allergens]}")
            
            try:
                db.session.commit()
                print("Changes committed successfully")
            except Exception as e:
                db.session.rollback()
                print(f"Error committing changes: {str(e)}")

if __name__ == "__main__":
    fix_allergen_relationships() 