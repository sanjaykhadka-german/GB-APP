# models/inventory.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import relationship
from database import db

class Inventory(db.Model):
    __tablename__ = 'inventory'

    id = db.Column(db.Integer, primary_key=True)
    week_commencing = db.Column(db.Date, nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)
    required_total = db.Column(db.Float, default=0.0)  # Total required for the week
    price_per_kg = db.Column(db.Float, default=0.0)    # From item_master
    value_required = db.Column(db.Float, default=0.0)   # required_total * price_per_kg
    current_stock = db.Column(db.Float, default=0.0)    # From raw_material_stocktake
    supplier_name = db.Column(db.String(255))           # From item_master

    # Relationship to ItemMaster
    item = db.relationship('ItemMaster', backref='inventories')
    
    def __repr__(self):
        return f'<Inventory {self.item_id} - Week {self.week_commencing}>'