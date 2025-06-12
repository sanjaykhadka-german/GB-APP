#insert joining data from excel to database


import pandas as pd
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Define the path to your Excel file
# Update this path to where your file is located on your local machine
excel_file_path = "joining_export.xlsx"

# Check if file exists
if not os.path.exists(excel_file_path):
    print(f"Error: File '{excel_file_path}' not found")
    exit(1)

# Read the Excel file
try:
    df = pd.read_excel(excel_file_path, sheet_name='Joining')
    print(f"Successfully loaded {len(df)} rows from 'Joining' sheet")
    
    # Print column names to debug
    print("\nAvailable columns in Excel:")
    print(df.columns.tolist())
    
    # Display the first few rows to verify the data structure
    print("\nFirst 5 rows of data:")
    print(df.head())
except Exception as e:
    print(f"Error reading Excel file: {e}")
    exit(1)

# Configure Flask app and database connection
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:german@localhost/gbdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define your model (matching your existing table)
class Joining(db.Model):
    __tablename__ = 'joining'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fg_code = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(255))
    fw = db.Column(db.Boolean, default=False)
    make_to_order = db.Column(db.Boolean, default=False)
    min_level = db.Column(db.Float)
    max_level = db.Column(db.Float)
    kg_per_unit = db.Column(db.Float)
    loss = db.Column(db.Float)
    filling_code = db.Column(db.String(50))
    filling_description = db.Column(db.String(255))
    production = db.Column(db.String(50))
    product_description = db.Column(db.String(255))
    units_per_bag = db.Column(db.Float, nullable=True)

# Helper function to safely convert to float
def safe_float(value):
    if pd.isna(value) or value == '':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

# Upload data to MySQL
with app.app_context():
    try:
        # Create tables if they don't exist
        print("Creating tables if they don't exist...")
        db.create_all()
        print("Tables created successfully")
        
        # Track progress
        total_rows = len(df)
        print(f"\nStarting to upload {total_rows} rows...")
        
        # First, clear existing data
        try:
            db.session.query(Joining).delete()
            db.session.commit()
            print("Cleared existing data from joining table")
        except Exception as e:
            print(f"Error clearing existing data: {e}")
            db.session.rollback()
            exit(1)
        
        skipped_rows = []
        
        # Insert data row by row
        for index, row in df.iterrows():
            try:
                # Handle potential NaN values
                row = row.fillna('')
                
                # Skip rows with empty FG Code
                fg_code = row['fg_code'] if not pd.isna(row['fg_code']) else ''
                if not fg_code or str(fg_code).strip() == '':
                    skipped_rows.append(index)
                    continue
                
                # Convert boolean columns properly
                fw_value = False
                if 'fw' in df.columns:
                    if pd.notna(row['fw']):
                        if isinstance(row['fw'], (int, float)):
                            fw_value = bool(row['fw'])
                        elif isinstance(row['fw'], str):
                            fw_value = row['fw'].lower() in ['yes', 'true', '1', 'y']
                
                mto_value = False
                if 'make_to_order' in df.columns:
                    if pd.notna(row['make_to_order']):
                        if isinstance(row['make_to_order'], (int, float)):
                            mto_value = bool(row['make_to_order'])
                        elif isinstance(row['make_to_order'], str):
                            mto_value = row['make_to_order'].lower() in ['yes', 'true', '1', 'y']
                
                # Create new record
                joining = Joining(
                    fg_code=str(fg_code).strip(),
                    description=str(row['description']) if not pd.isna(row['description']) else None,
                    fw=fw_value,
                    make_to_order=mto_value,
                    min_level=safe_float(row['min_level']),
                    max_level=safe_float(row['max_level']),
                    kg_per_unit=safe_float(row['kg_per_unit']),
                    loss=safe_float(row['loss']),
                    filling_code=str(row['filling_code']) if not pd.isna(row['filling_code']) else None,
                    filling_description=str(row['filling_description']) if not pd.isna(row['filling_description']) else None,
                    production=str(row['production']) if not pd.isna(row['production']) else None,
                    product_description=str(row['product_description']) if not pd.isna(row['product_description']) else None,
                    units_per_bag=safe_float(row['units_per_bag'])
                )
                
                db.session.add(joining)
                
                # Commit every 50 rows to avoid large transactions
                if (index + 1) % 50 == 0:
                    db.session.commit()
                    print(f"Processed {index + 1}/{total_rows} rows")
                    
            except Exception as e:
                print(f"Error processing row {index + 1} (FG Code: {fg_code}): {e}")
                skipped_rows.append(index)
                db.session.rollback()
                continue
        
        # Commit remaining changes
        try:
            db.session.commit()
            print("All data has been uploaded successfully!")
            if skipped_rows:
                print(f"\nSkipped {len(skipped_rows)} rows with issues:")
                for idx in skipped_rows:
                    print(f"Row {idx + 1}: FG Code = {df.iloc[idx].get('fg_code', 'empty')}")
        except Exception as e:
            db.session.rollback()
            print(f"Error committing final changes to database: {e}")
    except Exception as e:
        print(f"Error during database operations: {e}")
        if 'db' in locals():
            db.session.rollback()