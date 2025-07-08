from app import db
from datetime import datetime

class UsageReportTable(db.Model):
    __tablename__ = 'usage_report_table'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    week_commencing = db.Column(db.Date, nullable=False)
    production_date = db.Column(db.Date)
    recipe_code = db.Column(db.String(50))
    raw_material = db.Column(db.String(255))
    usage_kg = db.Column(db.Float)
    percentage = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<UsageReport {self.id} - {self.recipe_code}>' 