from app import app
from database import db
from models.item_master import ItemMaster
from models.allergen import Allergen

def check_allergens(item_id):
    with app.app_context():
        item = ItemMaster.query.get(item_id)
        if not item:
            print(f"No item found with ID {item_id}")
            return
        
        print(f"Item {item.item_code} (ID: {item.id}):")
        print(f"Current allergens: {[f'{a.name} (ID: {a.allergens_id})' for a in item.allergens]}")
        
        # Check item_allergen table directly
        from sqlalchemy import text
        result = db.session.execute(text(
            "SELECT a.allergens_id, a.name FROM allergen a "
            "JOIN item_allergen ia ON a.allergens_id = ia.allergen_id "
            "WHERE ia.item_id = :item_id"
        ), {"item_id": item_id})
        
        print("\nDirect allergen associations from item_allergen table:")
        for row in result:
            print(f"- {row.name} (ID: {row.allergens_id})")
        
        # List all available allergens
        print("\nAll available allergens:")
        allergens = Allergen.query.all()
        for allergen in allergens:
            print(f"- {allergen.name} (ID: {allergen.allergens_id})")

if __name__ == "__main__":
    check_allergens(240)  # Check allergens for item ID 240 