from database import db
from datetime import date

class UsageReport(db.Model):
    __tablename__ = 'usage_report'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    production_date = db.Column(db.Date, nullable=False)
    week_commencing = db.Column(db.Date)
    recipe_code = db.Column(db.String(50), nullable=False)
    raw_material = db.Column(db.String(255), nullable=False)
    usage_kg = db.Column(db.Float, nullable=False)
    percentage = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())