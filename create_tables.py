from flask import Flask
from database import db
from sqlalchemy import text, inspect
from models.allergen import Allergen
from models.category import Category
from models.department import Department
from models.machinery import Machinery
from models.uom import UOM
from models.item_master import ItemMaster
from models.recipe_master import RecipeMaster
from models.joining import Joining
from models.soh import SOH
from models.packing import Packing
from models.filling import Filling
from models.production import Production

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:german@localhost/gbdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def create_tables():
    with app.app_context():
        # Create tables one by one in proper order
        try:
            inspector = inspect(db.engine)
            
            # Disable foreign key checks
            db.session.execute(text('SET FOREIGN_KEY_CHECKS=0'))
            
            # Drop all tables
            tables = [
                'recipe_master', 'joining_allergen', 'item_allergen', 'joining',
                'soh', 'packing', 'filling', 'production', 'item_master',
                'allergen', 'category', 'department', 'machinery', 'uom_type'
            ]
            
            for table in tables:
                if inspector.has_table(table):
                    db.session.execute(text(f'DROP TABLE {table}'))
                    print(f"Dropped {table} table")
            
            # Re-enable foreign key checks
            db.session.execute(text('SET FOREIGN_KEY_CHECKS=1'))
            db.session.commit()
            print("Dropped existing tables")
            
            # First create base tables that don't depend on others
            Category.__table__.create(db.engine)
            print("Created category table")
            
            Department.__table__.create(db.engine)
            print("Created department table")
            
            Machinery.__table__.create(db.engine)
            print("Created machinery table")
            
            UOM.__table__.create(db.engine)
            print("Created UOM table")
            
            Allergen.__table__.create(db.engine)
            print("Created allergen table")

            # Create item_master table
            ItemMaster.__table__.create(db.engine)
            print("Created item_master table")

            # Create recipe_master table
            RecipeMaster.__table__.create(db.engine)
            print("Created recipe_master table")

            # Create operational tables
            Joining.__table__.create(db.engine)
            print("Created joining table")
            
            SOH.__table__.create(db.engine)
            print("Created soh table")
            
            Packing.__table__.create(db.engine)
            print("Created packing table")
            
            Filling.__table__.create(db.engine)
            print("Created filling table")
            
            Production.__table__.create(db.engine)
            print("Created production table")

            print("All tables created successfully!")

        except Exception as e:
            print(f"Error occurred: {e}")
            db.session.rollback()
            raise
        finally:
            # Make sure foreign key checks are re-enabled even if an error occurs
            db.session.execute(text('SET FOREIGN_KEY_CHECKS=1'))
            db.session.commit()

if __name__ == "__main__":
    create_tables() 