import pandas as pd
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Define the path to your Excel file
# Update this path to where your file is located on your local machine
excel_file_path = "Production_Plan_1.0.xlsm"

# Check if file exists
if not os.path.exists(excel_file_path):
    print(f"Error: File '{excel_file_path}' not found")
    exit(1)

# Read the Excel file
try:
    df = pd.read_excel(excel_file_path, sheet_name='Joining')
    print(f"Successfully loaded {len(df)} rows from 'Joining' sheet")
    
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
    fg_code = db.Column(db.String(50), nullable=False)
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

# Upload data to MySQL
with app.app_context():
    # Track progress
    total_rows = len(df)
    print(f"Starting to upload {total_rows} rows...")
    
    # Insert data row by row
    for index, row in df.iterrows():
        try:
            # Handle potential NaN values
            row = row.fillna('')
            
            # Convert boolean columns properly
            fw_value = False
            if 'FW' in df.columns:
                if pd.notna(row['FW']):
                    if isinstance(row['FW'], str):
                        fw_value = row['FW'].lower() in ['yes', 'true', '1', 'y']
                    else:
                        fw_value = bool(row['FW'])
            
            mto_value = False
            if 'MakeToOrder' in df.columns:
                if pd.notna(row['MakeToOrder']):
                    if isinstance(row['MakeToOrder'], str):
                        mto_value = row['MakeToOrder'].lower() in ['yes', 'true', '1', 'y']
                    else:
                        mto_value = bool(row['MakeToOrder'])
            
            # Create new record
            joining = Joining(
                fg_code=str(row['FG Code']) if 'FG Code' in df.columns and row['FG Code'] != '' else 'N/A',
                description=str(row['Description']) if 'Description' in df.columns and row['Description'] != '' else None,
                fw=fw_value,
                make_to_order=mto_value,
                min_level=float(row['Min Level']) if 'Min Level' in df.columns and row['Min Level'] != '' else None,
                max_level=float(row['Max Level']) if 'Max Level' in df.columns and row['Max Level'] != '' else None,
                kg_per_unit=float(row['kg/unit']) if 'kg/unit' in df.columns and row['kg/unit'] != '' else None,
                loss=float(row['Loss']) if 'Loss' in df.columns and row['Loss'] != '' else None,
                filling_code=str(row['Filling Code']) if 'Filling Code' in df.columns and row['Filling Code'] != '' else None,
                filling_description=str(row['Filling Description']) if 'Filling Description' in df.columns and row['Filling Description'] != '' else None,
                production=str(row['Production']) if 'Production' in df.columns and row['Production'] != '' else None
            )
            
            db.session.add(joining)
            
            # Print progress periodically
            if (index + 1) % 50 == 0 or index == total_rows - 1:
                print(f"Processed {index + 1}/{total_rows} rows")
                
        except Exception as e:
            print(f"Error processing row {index}: {e}")
            # Continue with next row instead of failing completely
            continue
    
    # Commit all changes at once
    try:
        db.session.commit()
        print("All data has been uploaded successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"Error committing changes to database: {e}")