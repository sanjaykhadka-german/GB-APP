from database import db
from datetime import datetime

class UsageReportTable(db.Model):
    __tablename__ = 'usage_report_table'

    id = db.Column(db.Integer, primary_key=True)
    week_commencing = db.Column(db.Date, nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)
    monday = db.Column(db.DECIMAL(10,2), default=0.00)
    tuesday = db.Column(db.DECIMAL(10,2), default=0.00)
    wednesday = db.Column(db.DECIMAL(10,2), default=0.00)
    thursday = db.Column(db.DECIMAL(10,2), default=0.00)
    friday = db.Column(db.DECIMAL(10,2), default=0.00)
    total_usage = db.Column(db.DECIMAL(10,2), default=0.00)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Relationships
    item = db.relationship('ItemMaster', backref='usage_reports')

    def __repr__(self):
        return f'<UsageReport {self.item.description} - {self.week_commencing}>' 