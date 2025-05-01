from database import db  # Assuming db is imported in app.py

class Packing(db.Model):
    __tablename__ = 'packing'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    packing_date = db.Column(db.Date, nullable=False)
    packing_code = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    units = db.Column(db.Float, default=0.0)
    total_kg = db.Column(db.Float, default=0.0)
    adjustment_kg = db.Column(db.Float, default=0.0)