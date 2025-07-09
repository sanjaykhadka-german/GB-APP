from database import db
from datetime import datetime

class RawMaterialReportTable(db.Model):
    __tablename__ = 'raw_material_report_table'

    id = db.Column(db.Integer, primary_key=True)
    week_commencing = db.Column(db.Date, nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)
    required_total_production = db.Column(db.DECIMAL(10,2), default=0.00)
    value_required_rm = db.Column(db.DECIMAL(10,2), default=0.00)
    current_stock = db.Column(db.DECIMAL(10,2), default=0.00)
    required_for_plan = db.Column(db.DECIMAL(10,2), default=0.00)
    variance_week = db.Column(db.DECIMAL(10,2), default=0.00)
    kg_required = db.Column(db.DECIMAL(10,2), default=0.00)
    variance = db.Column(db.DECIMAL(10,2), default=0.00)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Relationships
    item = db.relationship('ItemMaster', backref='raw_material_reports')

    def __repr__(self):
        return f'<RawMaterialReport {self.item.description} - {self.week_commencing}>' 
    
