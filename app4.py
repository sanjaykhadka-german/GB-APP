from decimal import Decimal
from flask import Flask
from database import db  # Your database module
from models import RecipeMaster  # Your RecipeMaster model

# Initialize Flask app
app = Flask(__name__)

# Configure your database URI (adjust this based on your setup)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:german@localhost/gbdb'  
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database with the app
db.init_app(app)

# Run the database operation within the app context
with app.app_context():
    # Recalculate all percentages
    recipes = RecipeMaster.query.all()
    for recipe in recipes:
        description = recipe.description
        total_kg = db.session.query(db.func.sum(RecipeMaster.kg_per_batch))\
            .filter(RecipeMaster.description == description)\
            .scalar() or 0
        if total_kg > 0:
            recipe.percentage = Decimal((float(recipe.kg_per_batch) / total_kg) * 100)
    db.session.commit()
    print("Percentages updated successfully.")