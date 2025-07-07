from database import db
from datetime import datetime

class RawMaterialReportTable(db.Model):
    __tablename__ = 'raw_material_report_table'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    production_date = db.Column(db.Date)
    week_commencing = db.Column(db.Date, nullable=False)
    raw_material = db.Column(db.String(255))
    meat_required = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    raw_material_id = db.Column(db.Integer)
    
    def __repr__(self):
        return f'<RawMaterialReport {self.id} - {self.raw_material}>' 