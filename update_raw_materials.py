from flask import Flask
from database import db
from models.raw_materials import RawMaterials
import os
from dotenv import load_dotenv
from sqlalchemy import text

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def update_raw_materials_table():
    with app.app_context():
        # Add raw_material_code column if it doesn't exist
        try:
            with db.engine.connect() as conn:
                # Add the column
                conn.execute(text("""
                    ALTER TABLE raw_materials 
                    ADD COLUMN raw_material_code VARCHAR(20) NULL AFTER id
                """))
                print("Added raw_material_code column")
                
                # Update existing rows with generated codes
                conn.execute(text("""
                    UPDATE raw_materials 
                    SET raw_material_code = CONCAT('RM', LPAD(id, 3, '0'))
                    WHERE raw_material_code IS NULL
                """))
                print("Updated existing rows with generated codes")
                
                # Make the column not nullable and unique
                conn.execute(text("""
                    ALTER TABLE raw_materials 
                    MODIFY COLUMN raw_material_code VARCHAR(20) NOT NULL,
                    ADD UNIQUE INDEX uq_raw_materials_code (raw_material_code)
                """))
                print("Made raw_material_code not nullable and unique")
                
        except Exception as e:
            print(f"Error: {str(e)}")
            if "Duplicate column name" in str(e):
                print("Column already exists, skipping creation")
            else:
                raise

if __name__ == '__main__':
    update_raw_materials_table() 