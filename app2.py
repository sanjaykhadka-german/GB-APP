import pandas as pd
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

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

class RecipeMaster(db.Model):
    __tablename__ = 'recipe_master'  # Fixed: double underscores
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    recipe_code = db.Column(db.String(100), nullable=False)
    Description = db.Column(db.String(255))
    raw_material = db.Column(db.String(100), nullable=False)
    kg_per_batch = db.Column(db.Float)
    percentage = db.Column(db.Float)

# Read the Excel file
try:
    df = pd.read_excel(excel_file_path, sheet_name='Recipe')
    print(f"Successfully loaded {len(df)} rows from 'Recipe' sheet")
    print("\nFirst 5 rows of data:")
    print(df.head())
    
    # Rename columns to match database field names
    df = df.rename(columns={
        'Recipe Code': 'recipe_code',
        'Description': 'Description',
        'Raw Material': 'raw_material',
        'KG per Batch': 'kg_per_batch',
        'Percentage': 'percentage'
    })
except Exception as e:
    print(f"Error reading Excel file: {e}")
    exit(1)

with app.app_context():
    # Option: Recreate the table (be careful in production!)
    # db.drop_all()
    db.create_all()
    
    # Execute ALTER TABLE if needed (uncomment if you want to use this approach)
    # db.engine.execute("ALTER TABLE recipe_master MODIFY id INT AUTO_INCREMENT;")
    
    total_rows = len(df)
    print(f"Starting to upload {total_rows} rows...")
    
    for index, row in df.iterrows():
        try:
            row = row.fillna('')
            # Check for required fields
            if ('recipe_code' not in df.columns or row['recipe_code'] == '' or
                'raw_material' not in df.columns or row['raw_material'] == ''):
                print(f"Skipping row {index}: Missing required field(s)")
                continue
                
            # Create new record (omitting id to let MySQL auto-generate it)
            recipe = RecipeMaster(
                recipe_code=str(row['recipe_code']),
                Description=str(row['Description']) if 'Description' in df.columns and row['Description'] != '' else None,
                raw_material=str(row['raw_material']),
                kg_per_batch=float(row['kg_per_batch']) if 'kg_per_batch' in df.columns and row['kg_per_batch'] != '' else None,
                percentage=float(row['percentage']) if 'percentage' in df.columns and row['percentage'] != '' else None
            )
            db.session.add(recipe)
            
            # Print progress periodically
            if (index + 1) % 50 == 0 or index == total_rows - 1:
                print(f"Processed {index + 1}/{total_rows} rows")
                
        except Exception as e:
            print(f"Error processing row {index}: {e}")
            continue
            
    # Commit all changes at once
    try:
        db.session.commit()
        print("All data has been uploaded successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"Error committing changes to database: {e}")