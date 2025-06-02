from models.allergen import Allergen
from app import app, db  # Make sure 'app' is your Flask app instance

allergens_to_add = [
    'cheese/milk',
    'gluten',
    'nitrite',
    'soy',
    'sulphite'
]

with app.app_context():
    for name in allergens_to_add:
        if not Allergen.query.filter_by(name=name).first():
            allergen = Allergen(name=name)
            db.session.add(allergen)
    db.session.commit()
