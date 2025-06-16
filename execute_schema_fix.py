#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from flask import Flask
from database import db
from models.packing import Packing
from models.soh import SOH
from models.machinery import Machinery
from models.joining import Joining
from models.filling import Filling
from models.production import Production
from models.recipe_master import RecipeMaster
from models.raw_materials import RawMaterials
from models.usage_report import UsageReport
from models.raw_material_report import RawMaterialReport
from models.item_master import ItemMaster
from sqlalchemy import text

def fix_packing_schema():
    # Load environment variables
    load_dotenv()
    
    # Create Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    with app.app_context():
        try:
            # Execute the schema fix
            print("Fixing packing table schema...")
            
            # Step 1: Drop the old unique constraint
            try:
                db.session.execute(text("ALTER TABLE packing DROP INDEX uq_packing_week_product"))
                print("✅ Dropped old unique constraint 'uq_packing_week_product'")
            except Exception as e:
                print(f"⚠️  Could not drop uq_packing_week_product: {e}")
            
            # Step 2: Drop the old primary key
            try:
                db.session.execute(text("ALTER TABLE packing DROP PRIMARY KEY"))
                print("✅ Dropped old primary key")
            except Exception as e:
                print(f"⚠️  Could not drop primary key: {e}")
            
            # Step 3: Add the new composite primary key
            try:
                db.session.execute(text("""
                    ALTER TABLE packing 
                    ADD PRIMARY KEY (week_commencing, packing_date, product_code, machinery)
                """))
                print("✅ Added new composite primary key")
            except Exception as e:
                print(f"❌ Error adding new primary key: {e}")
                return False
            
            # Commit the changes
            db.session.commit()
            
            # Step 4: Verify the changes
            print("\nVerifying table structure...")
            result = db.session.execute(text("SHOW CREATE TABLE packing"))
            table_info = result.fetchone()
            print("New table structure:")
            print(table_info[1])
            
            print("\n🎉 Schema fix completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error during schema fix: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    success = fix_packing_schema()
    if success:
        print("\nYou can now create packing entries without constraint errors.")
    else:
        print("\nSchema fix failed. Please check the error messages above.") 