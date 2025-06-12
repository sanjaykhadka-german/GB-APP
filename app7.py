from flask import Flask
from database import db
from models.item_master import ItemMaster

# Initialize Flask app
app = Flask(__name__)

# Configure your database (update with your MySQL credentials)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:german@localhost/gbdb'  # Update with your credentials
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize db with the app
db.init_app(app)

# List of finished goods (extracted from your recipe details)
finished_goods_list = [
    {"recipe_code": "2006", "description": "Frankfurter - WIP"},
    {"recipe_code": "6002", "description": "Veal Frankfurter Mix WIP"},
    {"recipe_code": "2005", "description": "Weisswurst - WIP"},
    {"recipe_code": "2002", "description": "Thuringer Bratwurst - WIP"},
    {"recipe_code": "20001", "description": "Chilli Con Carne WIP"},
    {"recipe_code": "2008", "description": "Debrecziner WIP"},
    {"recipe_code": "2015", "description": "Chorizo - WIP"},
    {"recipe_code": "3012", "description": "Leberkaes - WIP"},
    {"recipe_code": "2022", "description": "Chicken Blanched Chipolata - WIP"},
    {"recipe_code": "6004.6", "description": "Spekacky"},
    {"recipe_code": "2020", "description": "Beef Hot Dog - WIP"},
    {"recipe_code": "2033", "description": "Costco Tasty Juicy Hot Dogs NEW ZEALAND - WIP"},
    {"recipe_code": "2034", "description": "Majestic Hotdogs Regular - WIP"},
    {"recipe_code": "2032", "description": "Costco Tasty Juicy Hot Dogs DOMESTIC - WIP"},
    {"recipe_code": "2025", "description": "Chicken & Thyme Chipolata - WIP"},
    {"recipe_code": "2205", "description": "CFC Longganisa Sausage - WIP"},
    {"recipe_code": "2023", "description": "Italian Sausage - WIP"},
    {"recipe_code": "2038", "description": "MM - Beef Sausage - WIP"},
    {"recipe_code": "2039", "description": "MM - Pork Sausage - WIP"},
    {"recipe_code": "2204", "description": "CFC Carne Asada Beef Sausage - WIP"},
    {"recipe_code": "2045", "description": "Tailgate Pork Franks - WIP"},
    {"recipe_code": "1010", "description": "Charsu Pork Neck - WIP"},
    {"recipe_code": "1004", "description": "HF diced Bacon Logs - WIP"},
    {"recipe_code": "1024.4000.1", "description": "4x4 HAM"},
    {"recipe_code": "1024", "description": "Costco Ham WIP"},
    {"recipe_code": "10003", "description": "Pulled Beef - WIP"},
    {"recipe_code": "1007GB", "description": "Pulled Pork GB WIP"},
    {"recipe_code": "9004", "description": "Hocks WIP"},
    {"recipe_code": "1003", "description": "Ham - WIP"},
    {"recipe_code": "1003.8", "description": "Ham Slicing Log - Whole"},
    {"recipe_code": "1005", "description": "Pan Size WIP"}
]

# Run within application context
with app.app_context():
    # Insert finished goods
    for fg in finished_goods_list:
        item_code = fg["recipe_code"]
        
        # Check if finished good already exists to avoid duplicates
        existing_item = db.session.query(ItemMaster).filter_by(item_code=item_code).first()
        if existing_item:
            print(f"Finished good '{item_code}' already exists. Skipping.")
            continue
        
        # Create ItemMaster entry for finished good
        item = ItemMaster(
            item_code=item_code,
            description=fg["description"],
            item_type='finished_good',
            category_id=None,  # Adjust based on your category table
            department_id=None,  # Adjust based on your department table
            uom_id=None,  # Adjust based on your UOM table
            min_level=0.0,  # Adjust as needed
            max_level=100.0,  # Adjust as needed
            is_make_to_order=False,  # Adjust as needed
            kg_per_unit=0.0,  # Adjust as needed
            units_per_bag=0.0,  # Adjust as needed
            loss_percentage=0.0,  # Adjust as needed
            is_active=True
        )
        db.session.add(item)
    
    # Commit the transaction
    try:
        db.session.commit()
        print("Finished goods inserted successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"Error inserting finished goods: {e}")

if __name__ == '__main__':
    app.run(debug=True)  # Optional: only if you want to run the Flask app