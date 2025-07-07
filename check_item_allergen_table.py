from app import app
from database import db
from sqlalchemy import text

def check_item_allergen_table():
    with app.app_context():
        # Check direct entries in item_allergen table
        result = db.session.execute(text("""
            SELECT ia.item_id, ia.allergen_id, a.name as allergen_name, im.item_code
            FROM item_allergen ia
            JOIN allergen a ON a.allergens_id = ia.allergen_id
            LEFT JOIN item_master im ON im.id = ia.item_id
            ORDER BY ia.item_id
        """))
        
        print("\nDirect entries in item_allergen table:")
        for row in result:
            print(f"Item {row.item_code} (ID: {row.item_id}) -> {row.allergen_name} (ID: {row.allergen_id})")
        
        # Check specific item 2006.1
        result = db.session.execute(text("""
            SELECT ia.item_id, ia.allergen_id, a.name as allergen_name
            FROM item_allergen ia
            JOIN allergen a ON a.allergens_id = ia.allergen_id
            WHERE ia.item_id = 240
        """))
        
        print("\nAllergens for item ID 240 (2006.1):")
        rows = list(result)
        if not rows:
            print("No allergens found")
        for row in rows:
            print(f"- {row.allergen_name} (ID: {row.allergen_id})")

if __name__ == "__main__":
    check_item_allergen_table() 