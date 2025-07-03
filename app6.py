# from flask import Flask
# from database import db  # Your database module
# from models.item_master import ItemMaster

# # Initialize Flask app
# app = Flask(__name__)

# # Configure your database (adjust URI as per your setup)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:german@localhost/gbdb'  # Update with your MySQL credentials
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# # Initialize db with the app
# db.init_app(app)

# # List of raw materials
# raw_materials_list = [
#     "Pork 80CL", "Pork Jowls", "Ice", "Chicken MDM", "Salt", "Ultra Cure/hi cure",
#     "Vienna Gold", "STPP", "Fresh Red", "ISP", "Potato Starch", "Colorado CM",
#     "Garlic Powder", "Frischex", "Sodium Lactate", "Veal Trim", "Chicken Skin",
#     "Chicken Trimming", "Pork 75 CL", "Pork Back Fat", "Zitromat (Raps)",
#     "dried parsely", "Pepper White Ground", "Weisswurst Spice", "Onion Powder",
#     "Preservative", "Sugar Raw", "Nutmeg Ground", "Caraway Ground",
#     "Gluta Clean (Raps)", "Majoram", "Pork Top Site SSF", "Water",
#     "Red Kidney Beans", "Minced Chilli", "Pepper black Ground", "Onion Fresh diced",
#     "Tomato Paste", "Novation 2600", "Emulsan KW1000", "Fermex (GM)",
#     "Paprika Liquid 100.000", "Debreziner Spice (RAPS)", "Chilli Ground",
#     "Sodium Erythorbate", "Chorizo Spice (RAPS)", "Pork Fat (Shoulder & Leg)",
#     "Meat Loaf Laudatio", "Onions fresh", "GF Premix Chicken F25A",
#     "Krainer Sausage Spice", "Beef 75CL", "Spiess Fat", "Emulsion Trim",
#     "Fermented Rice", "Water Iced (below 1⁰C)", "JMT Frankfurter EZY Mix",
#     "FUMARO", "Rice Flour", "Mace Ground", "Thyme",
#     "Preservative Dry Sodium Sulphite 25kg", "Filipino Longanisa Premix", "Citrat",
#     "Paprika", "Paprika Aqua Spice stable 15kg", "Beef 80CL", "MSG",
#     "GF Barbecue ASADA RUB", "Sodium Bicarbonate", "Dextrose Monohydrate",
#     "Mustard Powder", "Paprika 3000 (Raps)", "Scansmoke PB-1200 25kg",
#     "Pork Neck BL/RL", "Charsu Rap", "Schiadit", "Schinko", "Diaphgram",
#     "Pork Topside", "Pork Shoulder", "Colflo", "Beef 90CL", "Chilli Flakes Dry",
#     "Pork Hock", "Pork 2 Piece Leg",
#     "Pork Loin RL pan size square cut 200mm width total", "Pepper Extract"
# ]

# # Run within application context
# with app.app_context():
#     # Insert raw materials
#     for index, raw_material_name in enumerate(raw_materials_list, start=1):
#         # Generate item_code: RM0001, RM0002, etc.
#         item_code = f"RM{str(index).zfill(4)}"
        
#         # Check if raw material already exists to avoid duplicates
#         existing_item = db.session.query(ItemMaster).filter_by(item_code=item_code).first()
#         if existing_item:
#             continue
        
#         # Create ItemMaster entry
#         item = ItemMaster(
#             item_code=item_code,
#             description=raw_material_name,
#             item_type='raw_material',
#             category_id=1,  # Adjust based on your category table
#             department_id=1,  # Adjust based on your department table
#             uom_id=1,  # Adjust based on your UOM table (e.g., for 'kg')
#             min_level=0.0,  # Adjust as needed
#             max_level=100.0,  # Adjust as needed
#             price_per_kg=0.0,  # Set price if available
#             is_active=True
#         )
#         db.session.add(item)
        
#         # Create RawMaterials entry
#         raw_material = RawMaterials(
#             raw_material_code=item_code,  # Same as item_code
#             raw_material=raw_material_name,
#             description=raw_material_name,
#             category_id=1,  # Adjust as needed
#             department_id=1,  # Adjust as needed
#             uom_id=1,  # Adjust as needed
#             min_level=0.0,  # Adjust as needed
#             max_level=100.0,  # Adjust as needed
#             price_per_kg=0.0,  # Set price if available
#             is_active=True
#         )
#         db.session.add(raw_material)
    
#     # Commit the transaction
#     try:
#         db.session.commit()
#         print("Raw materials inserted successfully.")
#     except Exception as e:
#         db.session.rollback()
#         print(f"Error inserting raw materials: {e}")

# if __name__ == '__main__':
#     app.run(debug=True)  # Optional: only if you want to run the Flask app