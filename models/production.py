from database import db  # Assuming db is imported in app.py

class Production(db.Model):
    __tablename__ = 'production'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    week_commencing = db.Column(db.Date, nullable=True)  # New column
    production_date = db.Column(db.Date, nullable=False)
    production_code = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    batches = db.Column(db.Float, default=0.0)
    total_kg = db.Column(db.Float, default=0.0)