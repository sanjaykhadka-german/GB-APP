from database import db

class RecipeMaster(db.Model):
    __tablename__ = 'recipe_master'  # Fixed: double underscores
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    recipe_code = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    raw_material = db.Column(db.String(100), nullable=False)
    kg_per_batch = db.Column(db.Float)
    percentage = db.Column(db.Float)