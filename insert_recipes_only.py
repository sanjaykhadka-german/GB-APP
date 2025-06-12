from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os
from datetime import datetime

# Path to your Excel file
excel_file_path = "Production_Plan_1.0.xlsm"

# Check if file exists
if not os.path.exists(excel_file_path):
    print(f"Error: File '{excel_file_path}' not found")
    exit(1)

# Configure Flask app and database connection
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:german@localhost/gbdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class ItemMaster(db.Model):
    __tablename__ = 'item_master'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.String(255))
    item_type = db.Column(db.String(20))

class RecipeMaster(db.Model):
    __tablename__ = 'recipe_master'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    recipe_code = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    raw_material_id = db.Column(db.Integer, db.ForeignKey('item_master.id', ondelete='CASCADE'), nullable=False)
    finished_good_id = db.Column(db.Integer, db.ForeignKey('item_master.id', ondelete='CASCADE'), nullable=False)
    kg_per_batch = db.Column(db.Float)
    percentage = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

with app.app_context():
    try:
        # First, clear existing data
        print("\nClearing existing data from recipe_master table...")
        db.session.query(RecipeMaster).delete()
        db.session.commit()
        print("Existing data cleared successfully")

        # Read the Excel file
        df = pd.read_excel(excel_file_path, sheet_name='Recipe')
        print(f"Successfully loaded {len(df)} rows from 'Recipe' sheet")

        # Get all existing raw materials and finished goods
        raw_materials = {item.description: item for item in ItemMaster.query.filter_by(item_type='raw_material').all()}
        finished_goods = ItemMaster.query.filter_by(item_type='finished_good').all()

        # Create a mapping from item code to finished good
        item_code_to_fg = {}
        for fg in finished_goods:
            item_code_to_fg[fg.item_code] = fg

        # Also create a mapping from recipe code to finished good
        recipe_code_to_fg = {}
        for fg in finished_goods:
            recipe_code = fg.description.split(' - ')[0].strip()
            recipe_code_to_fg[recipe_code] = fg

        print(f"\nFound {len(raw_materials)} raw materials and {len(finished_goods)} finished goods in database")
        print("Item codes mapped:", list(item_code_to_fg.keys()))
        print("Recipe codes mapped:", list(recipe_code_to_fg.keys()))

        # Process recipes
        print("\nProcessing recipes...")
        skipped_rows = []
        processed_rows = 0

        for index, row in df.iterrows():
            try:
                raw_material = raw_materials.get(row['Raw Material'])
                recipe_code = str(row['Recipe Code'])
                
                # Try to find the finished good by recipe code first
                finished_good = recipe_code_to_fg.get(recipe_code)
                if not finished_good:
                    # If not found, try by item code
                    finished_good = item_code_to_fg.get(recipe_code)
                
                if not raw_material or not finished_good:
                    reason = []
                    if not raw_material:
                        reason.append(f"raw material '{row['Raw Material']}' not found")
                    if not finished_good:
                        reason.append(f"finished good '{recipe_code}' not found")
                    skipped_rows.append((index + 2, ", ".join(reason)))
                    continue

                recipe = RecipeMaster(
                    recipe_code=recipe_code,
                    description=row['Description'],
                    raw_material_id=raw_material.id,
                    finished_good_id=finished_good.id,
                    kg_per_batch=row['KG per Batch'],
                    percentage=row['Percentage'],
                    is_active=True
                )
                db.session.add(recipe)
                processed_rows += 1

                # Commit every 100 rows
                if processed_rows % 100 == 0:
                    db.session.commit()
                    print(f"Processed {processed_rows} recipes...")

            except Exception as e:
                skipped_rows.append((index + 2, str(e)))
                continue

        # Final commit
        db.session.commit()

        print(f"\nSuccessfully processed {processed_rows} recipes")
        if skipped_rows:
            print("\nSkipped rows:")
            for row_num, reason in skipped_rows:
                print(f"Row {row_num}: {reason}")

    except Exception as e:
        print(f"Error: {e}")
        db.session.rollback() 