from database import db

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
    weekly_average = db.Column(db.Float, nullable=True)

    allergens = db.relationship('Allergen', secondary='joining_allergen', backref=db.backref('joinings', lazy='dynamic'))

    def __repr__(self):
        return f"<Joining {self.fg_code}>"