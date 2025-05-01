from database import db


class Allergen(db.Model):

    __tablename__ = 'allergen'
    allergens_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)