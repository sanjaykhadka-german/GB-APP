# models/inventory.py
from database import db
from datetime import datetime

class Inventory(db.Model):
    """
    Inventory model for tracking raw material requirements and stock levels
    """
    __tablename__ = 'inventory'

    id = db.Column(db.Integer, primary_key=True)
    week_commencing = db.Column(db.Date, nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)
    
    # Required in TOTAL for production (from raw_material_report_table)
    required_total = db.Column(db.Float)
    
    # Item details from item_master
    category = db.Column(db.String(100))
    price_per_kg = db.Column(db.Float)
    value_required = db.Column(db.Float)  # required_total * price_per_kg
    current_stock = db.Column(db.Float)  # from raw_material_stocktake
    supplier_name = db.Column(db.String(255))
    
    # Daily requirements (fixed values for now)
    monday = db.Column(db.Float, default=0)
    tuesday = db.Column(db.Float, default=0)
    wednesday = db.Column(db.Float, default=0)
    thursday = db.Column(db.Float, default=0)
    friday = db.Column(db.Float, default=0)
    saturday = db.Column(db.Float, default=0)
    sunday = db.Column(db.Float, default=0)
    
    # Calculated fields
    required_for_plan = db.Column(db.Float)  # Sum of daily values
    variance_for_week = db.Column(db.Float)  # current_stock - required_for_plan
    variance = db.Column(db.Float)  # current_stock - required_total
    to_be_ordered = db.Column(db.Float)
    closing_stock = db.Column(db.Float)
    
    # Relationships
    item = db.relationship('ItemMaster', backref='inventory_entries')
    
    def __repr__(self):
        return f"<Inventory {self.item.item_code} for week {self.week_commencing}>"
    
    @property
    def calculate_required_for_plan(self):
        """Calculate sum of daily requirements"""
        return sum(filter(None, [
            self.monday,
            self.tuesday,
            self.wednesday,
            self.thursday,
            self.friday,
            self.saturday,
            self.sunday
        ]))
    
    @property
    def calculate_value_required(self):
        """Calculate value required based on price per kg"""
        if self.required_total is not None and self.price_per_kg is not None:
            return self.required_total * self.price_per_kg
        return None
    
    @property
    def calculate_variance_for_week(self):
        """Calculate variance for week"""
        if self.current_stock is not None and self.required_for_plan is not None:
            return self.current_stock - self.required_for_plan
        return None
    
    @property
    def calculate_variance(self):
        """Calculate variance"""
        if self.current_stock is not None and self.required_total is not None:
            return self.current_stock - self.required_total
        return None