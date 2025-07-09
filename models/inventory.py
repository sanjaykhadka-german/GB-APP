# models/inventory.py
from database import db
from datetime import datetime
from sqlalchemy.orm import relationship

class Inventory(db.Model):
    __tablename__ = 'inventory'

    id = db.Column(db.Integer, primary_key=True)
    week_commencing = db.Column(db.Date, nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    price_per_kg = db.Column(db.DECIMAL(10,2), default=0.00)
    required_total_production = db.Column(db.DECIMAL(10,2), default=0.00)
    value_required_rm = db.Column(db.DECIMAL(10,2), default=0.00)
    current_stock = db.Column(db.DECIMAL(10,2), default=0.00)
    required_for_plan = db.Column(db.DECIMAL(10,2), default=0.00)
    variance_week = db.Column(db.DECIMAL(10,2), default=0.00)
    kg_required = db.Column(db.DECIMAL(10,2), default=0.00)
    variance = db.Column(db.DECIMAL(10,2), default=0.00)
    to_be_ordered = db.Column(db.DECIMAL(10,2), default=0.00)
    closing_stock = db.Column(db.DECIMAL(10,2), default=0.00)
    
    # Daily columns for requirements/usage
    monday = db.Column(db.DECIMAL(10,2), default=0.00)
    tuesday = db.Column(db.DECIMAL(10,2), default=0.00)
    wednesday = db.Column(db.DECIMAL(10,2), default=0.00)
    thursday = db.Column(db.DECIMAL(10,2), default=0.00)
    friday = db.Column(db.DECIMAL(10,2), default=0.00)
    saturday = db.Column(db.DECIMAL(10,2), default=0.00)
    sunday = db.Column(db.DECIMAL(10,2), default=0.00)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Relationships
    item = db.relationship('ItemMaster', backref='inventories')
    category = db.relationship('Category', backref='inventories')

    def calculate_value_required_rm(self):
        """Calculate $ Value for Required RM (F2 = C2 * E2)"""
        return float(self.required_total_production or 0) * float(self.price_per_kg or 0)

    def calculate_variance_week(self):
        """Calculate Variance for the week (J2 = G2 - I2)"""
        try:
            return float(self.current_stock or 0) - float(self.required_for_plan or 0)
        except:
            return 0.00

    def calculate_variance(self):
        """Calculate Variance (L2 = G2 - K2)"""
        try:
            return float(self.current_stock or 0) - float(self.kg_required or 0)
        except:
            return 0.00

    def calculate_weekly_total(self):
        """Calculate total from daily requirements"""
        daily_values = [
            float(self.monday or 0),
            float(self.tuesday or 0),
            float(self.wednesday or 0),
            float(self.thursday or 0),
            float(self.friday or 0),
            float(self.saturday or 0),
            float(self.sunday or 0)
        ]
        return sum(daily_values)

    def __repr__(self):
        return f'<Inventory {self.item.description} - {self.week_commencing}>'