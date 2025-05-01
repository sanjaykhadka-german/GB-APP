from database import db  # Assuming db is imported in app.py

class Filling(db.Model):
    __tablename__ = 'filling'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filling_date = db.Column(db.Date, nullable=False)
    fill_code = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    kilo_per_size = db.Column(db.Float, default=0.0)