from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:german@localhost/gbdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

with app.app_context():
    # First, let's check what entries we're going to delete
    check_query = text("""
        SELECT id, item_code, description, item_type, is_active
        FROM item_master
        WHERE description IS NULL 
        OR description = ''
        OR TRIM(description) = '';
    """)
    
    print("\nEntries to be deleted:")
    entries = db.session.execute(check_query).fetchall()
    for entry in entries:
        print(f"ID: {entry.id}, Code: {entry.item_code}, Type: {entry.item_type}, Active: {entry.is_active}")
    
    if entries:
        print(f"\nFound {len(entries)} entries with null/empty descriptions.")
        print("Checking for recipe dependencies...")
        
        # Check for recipe_master dependencies
        recipe_check_query = text("""
            SELECT rm.id, rm.recipe_code, rm.raw_material_id, rm.finished_good_id,
                   im.item_code, im.description
            FROM recipe_master rm
            JOIN item_master im ON (rm.raw_material_id = im.id OR rm.finished_good_id = im.id)
            WHERE im.description IS NULL 
            OR im.description = ''
            OR TRIM(im.description) = '';
        """)
        
        dependent_recipes = db.session.execute(recipe_check_query).fetchall()
        if dependent_recipes:
            print("\nWarning: Found recipes using these items:")
            for recipe in dependent_recipes:
                print(f"Recipe ID: {recipe.id}, Code: {recipe.recipe_code}, Item: {recipe.item_code}")
            print("\nPlease handle recipe dependencies first.")
        else:
            # Delete the entries
            delete_query = text("""
                DELETE FROM item_master
                WHERE description IS NULL 
                OR description = ''
                OR TRIM(description) = '';
            """)
            
            try:
                result = db.session.execute(delete_query)
                db.session.commit()
                print(f"\nSuccessfully deleted {result.rowcount} entries")
            except Exception as e:
                db.session.rollback()
                print(f"\nError deleting entries: {e}")
    else:
        print("\nNo entries found with null/empty descriptions.") 