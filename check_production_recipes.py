from flask import Flask
from database import db
from sqlalchemy.sql import text
from models import Production, RecipeMaster, RawMaterials, UsageReport
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:german@localhost/gbdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Validate SQLALCHEMY_DATABASE_URI
if not app.config['SQLALCHEMY_DATABASE_URI']:
    raise RuntimeError(
        "SQLALCHEMY_DATABASE_URI is not set. Please define it in the .env file or environment variables."
    )

db.init_app(app)

def check_production_recipes():
    with app.app_context():
        # Get all production records
        productions = Production.query.all()
        print("\nChecking production codes against recipe codes...")
        print(f"Total production records: {len(productions)}")
        
        for prod in productions:
            print(f"\nProduction Code: {prod.production_code}")
            print(f"Date: {prod.production_date}")
            print(f"Total KG: {prod.total_kg}")
            
            # Find matching recipes
            recipes = RecipeMaster.query.filter_by(recipe_code=prod.production_code).all()
            print(f"Matching Recipes: {len(recipes)}")
            
            if recipes:
                print("Recipe details:")
                total_kg_per_batch = 0
                for recipe in recipes:
                    print(f"- Raw Material: {recipe.raw_material_id}")
                    print(f"  KG per batch: {recipe.kg_per_batch}")
                    print(f"  Percentage: {recipe.percentage}")
                    total_kg_per_batch += recipe.kg_per_batch
                print(f"Total KG per batch: {total_kg_per_batch}")
            else:
                print("WARNING: No matching recipes found!")
                
                # Check for similar recipe codes
                similar_recipes = RecipeMaster.query.filter(
                    RecipeMaster.recipe_code.like(f"%{prod.production_code}%")
                ).all()
                if similar_recipes:
                    print("Similar recipe codes found:")
                    for recipe in similar_recipes:
                        print(f"- {recipe.recipe_code}")

        # Check for any recipe codes that don't have matching production codes
        all_recipe_codes = db.session.query(RecipeMaster.recipe_code).distinct().all()
        all_recipe_codes = [code[0] for code in all_recipe_codes]
        all_production_codes = [p.production_code for p in productions]
        
        unmatched_recipes = set(all_recipe_codes) - set(all_production_codes)
        if unmatched_recipes:
            print("\nRecipe codes without matching production codes:")
            for code in sorted(unmatched_recipes):
                print(f"- {code}")

if __name__ == '__main__':
    check_production_recipes() 