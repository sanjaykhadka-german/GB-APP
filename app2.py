#insert recipe master data from excel to database

import pandas as pd
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
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

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)

class Department(db.Model):
    __tablename__ = 'department'
    department_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    departmentName = db.Column(db.String(50), nullable=False, unique=True)

class UOM(db.Model):
    __tablename__ = 'uom_type'
    UOMID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UOMName = db.Column(db.String(50), nullable=False)

class Machinery(db.Model):
    __tablename__ = 'machinery'
    machineID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    machineryName = db.Column(db.String(50), nullable=False)

class ItemMaster(db.Model):
    __tablename__ = 'item_master'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.String(255))
    item_type = db.Column(db.String(20))  # 'raw_material' or 'finished_good'
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    department_id = db.Column(db.Integer, db.ForeignKey('department.department_id'))
    machinery_id = db.Column(db.Integer, db.ForeignKey('machinery.machineID'))
    uom_id = db.Column(db.Integer, db.ForeignKey('uom_type.UOMID'))
    min_level = db.Column(db.Float)
    max_level = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Relationships
    category = db.relationship('Category', backref='items')
    department = db.relationship('Department', backref='items')
    machinery = db.relationship('Machinery', backref='items')
    uom = db.relationship('UOM', backref='items')

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

    # Relationships
    raw_material = db.relationship('ItemMaster', foreign_keys=[raw_material_id], backref='recipes_as_raw_material')
    finished_good = db.relationship('ItemMaster', foreign_keys=[finished_good_id], backref='recipes_as_finished_good')

# Read the Excel file
try:
    # Read the Excel file
    df = pd.read_excel(excel_file_path, sheet_name='Recipe')
    print(f"Successfully loaded {len(df)} rows from 'Recipe' sheet")
    
    # Print column names for debugging
    print("\nAvailable columns in Excel:")
    print(df.columns.tolist())
    
    # Print data types of columns
    print("\nData types of columns:")
    print(df.dtypes)
    
    # Print first few rows with all columns
    pd.set_option('display.max_columns', None)
    print("\nFirst 5 rows of data (all columns):")
    print(df.head())
    
    # Check for missing required columns
    required_columns = ['Recipe Code', 'Description', 'Raw Material', 'KG per Batch', 'Percentage']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"\nError: Missing required columns: {missing_columns}")
        exit(1)
    
    # Rename columns to match database field names
    df = df.rename(columns={
        'Recipe Code': 'recipe_code',
        'Description': 'description',
        'Raw Material': 'raw_material',
        'KG per Batch': 'kg_per_batch',
        'Percentage': 'percentage'
    })
    
    # Convert numeric columns to float, replacing any non-numeric values with NaN
    if 'kg_per_batch' in df.columns:
        df['kg_per_batch'] = pd.to_numeric(df['kg_per_batch'], errors='coerce')
    if 'percentage' in df.columns:
        df['percentage'] = pd.to_numeric(df['percentage'], errors='coerce')
    
except Exception as e:
    print(f"Error reading Excel file: {e}")
    exit(1)

def generate_item_code(item_name, item_type, index):
    """Generate a unique code for items that's under 20 characters"""
    # Remove special characters and spaces
    base = ''.join(e for e in item_name if e.isalnum())[:10]
    # Add prefix based on type and a number to ensure uniqueness
    prefix = "RM" if item_type == "raw_material" else "FG"
    return f"{prefix}{index:04d}"

with app.app_context():
    try:
        # Create tables if they don't exist
        print("\nCreating tables if they don't exist...")
        db.create_all()
        print("Tables created successfully")

        # First, clear existing data
        print("\nClearing existing data from recipe_master table...")
        db.session.query(RecipeMaster).delete()
        db.session.commit()
        print("Existing data cleared successfully")

        # Create default category, department and UOM if they don't exist
        default_category = Category.query.filter_by(name='Default').first()
        if not default_category:
            default_category = Category(name='Default')
            db.session.add(default_category)

        default_department = Department.query.filter_by(departmentName='Default').first()
        if not default_department:
            default_department = Department(departmentName='Default')
            db.session.add(default_department)

        default_uom = UOM.query.filter_by(UOMName='KG').first()
        if not default_uom:
            default_uom = UOM(UOMName='KG')
            db.session.add(default_uom)

        db.session.commit()

        # Get unique raw materials and finished goods first and create mappings
        unique_raw_materials = sorted(df['raw_material'].unique())
        unique_recipes = sorted(df['recipe_code'].unique())
        raw_material_mapping = {}
        finished_good_mapping = {}
        
        print("\nProcessing raw materials...")
        for idx, raw_material_name in enumerate(unique_raw_materials, 1):
            try:
                # Generate a unique code for this raw material
                item_code = generate_item_code(raw_material_name, "raw_material", idx)
                
                # Check if raw material already exists
                item = ItemMaster.query.filter(
                    (ItemMaster.item_code == item_code) | 
                    ((ItemMaster.description == raw_material_name) & (ItemMaster.item_type == 'raw_material'))
                ).first()
                
                if not item:
                    item = ItemMaster(
                        item_code=item_code,
                        description=raw_material_name,
                        item_type='raw_material',
                        category_id=default_category.id,
                        department_id=default_department.department_id,
                        uom_id=default_uom.UOMID,
                        min_level=0,
                        max_level=0,
                        is_active=True
                    )
                    db.session.add(item)
                    db.session.flush()
                
                raw_material_mapping[raw_material_name] = item
                
            except Exception as e:
                print(f"Error processing raw material '{raw_material_name}': {e}")
                continue

        print("\nProcessing finished goods...")
        for idx, recipe_code in enumerate(unique_recipes, 1):
            try:
                # Get the description from the first matching recipe
                recipe_desc = df[df['recipe_code'] == recipe_code]['description'].iloc[0]
                
                # Generate a unique code for this finished good
                item_code = generate_item_code(recipe_code, "finished_good", idx)
                
                # Check if finished good already exists
                item = ItemMaster.query.filter(
                    (ItemMaster.item_code == item_code) | 
                    ((ItemMaster.description == recipe_code) & (ItemMaster.item_type == 'finished_good'))
                ).first()
                
                if not item:
                    item = ItemMaster(
                        item_code=item_code,
                        description=recipe_desc,
                        item_type='finished_good',
                        category_id=default_category.id,
                        department_id=default_department.department_id,
                        uom_id=default_uom.UOMID,
                        min_level=0,
                        max_level=0,
                        is_active=True
                    )
                    db.session.add(item)
                    db.session.flush()
                
                finished_good_mapping[recipe_code] = item
                
            except Exception as e:
                print(f"Error processing finished good '{recipe_code}': {e}")
                continue
        
        db.session.commit()
        print(f"Processed {len(raw_material_mapping)} raw materials and {len(finished_good_mapping)} finished goods")

        # Now process recipes
        print("\nProcessing recipes...")
        skipped_rows = []
        processed_rows = 0

        for index, row in df.iterrows():
            try:
                raw_material = raw_material_mapping.get(row['raw_material'])
                finished_good = finished_good_mapping.get(row['recipe_code'])
                
                if not raw_material or not finished_good:
                    reason = []
                    if not raw_material:
                        reason.append(f"raw material '{row['raw_material']}' not found")
                    if not finished_good:
                        reason.append(f"finished good '{row['recipe_code']}' not found")
                    skipped_rows.append((index + 2, ", ".join(reason)))
                    continue

                recipe = RecipeMaster(
                    recipe_code=row['recipe_code'],
                    description=row['description'],
                    raw_material_id=raw_material.id,
                    finished_good_id=finished_good.id,
                    kg_per_batch=row['kg_per_batch'],
                    percentage=row['percentage'],
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