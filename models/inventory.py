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

    # Weekly Summary Columns
    required_in_total = db.Column(db.Float, default=0.0)
    price_per_kg = db.Column(db.Float, default=0.0)
    value_required_rm = db.Column(db.Float, default=0.0)
    soh = db.Column(db.Float, default=0.0)
    supplier_name = db.Column(db.String(255))
    required_for_plan = db.Column(db.Float, default=0.0)
    variance_week = db.Column(db.Float, default=0.0)

    # Daily Columns
    monday_opening_stock = db.Column(db.Float, default=0.0)
    monday_required_kg = db.Column(db.Float, default=0.0)
    monday_variance = db.Column(db.Float, default=0.0)
    monday_to_be_ordered = db.Column(db.Float, default=0.0)
    monday_ordered_received = db.Column(db.Float, default=0.0)
    monday_consumed_kg = db.Column(db.Float, default=0.0)
    monday_closing_stock = db.Column(db.Float, default=0.0)

    tuesday_opening_stock = db.Column(db.Float, default=0.0)
    tuesday_required_kg = db.Column(db.Float, default=0.0)
    tuesday_variance = db.Column(db.Float, default=0.0)
    tuesday_to_be_ordered = db.Column(db.Float, default=0.0)
    tuesday_ordered_received = db.Column(db.Float, default=0.0)
    tuesday_consumed_kg = db.Column(db.Float, default=0.0)
    tuesday_closing_stock = db.Column(db.Float, default=0.0)

    wednesday_opening_stock = db.Column(db.Float, default=0.0)
    wednesday_required_kg = db.Column(db.Float, default=0.0)
    wednesday_variance = db.Column(db.Float, default=0.0)
    wednesday_to_be_ordered = db.Column(db.Float, default=0.0)
    wednesday_ordered_received = db.Column(db.Float, default=0.0)
    wednesday_consumed_kg = db.Column(db.Float, default=0.0)
    wednesday_closing_stock = db.Column(db.Float, default=0.0)

    thursday_opening_stock = db.Column(db.Float, default=0.0)
    thursday_required_kg = db.Column(db.Float, default=0.0)
    thursday_variance = db.Column(db.Float, default=0.0)
    thursday_to_be_ordered = db.Column(db.Float, default=0.0)
    thursday_ordered_received = db.Column(db.Float, default=0.0)
    thursday_consumed_kg = db.Column(db.Float, default=0.0)
    thursday_closing_stock = db.Column(db.Float, default=0.0)

    friday_opening_stock = db.Column(db.Float, default=0.0)
    friday_required_kg = db.Column(db.Float, default=0.0)
    friday_variance = db.Column(db.Float, default=0.0)
    friday_to_be_ordered = db.Column(db.Float, default=0.0)
    friday_ordered_received = db.Column(db.Float, default=0.0)
    friday_consumed_kg = db.Column(db.Float, default=0.0)
    friday_closing_stock = db.Column(db.Float, default=0.0)

    saturday_opening_stock = db.Column(db.Float, default=0.0)
    saturday_required_kg = db.Column(db.Float, default=0.0)
    saturday_variance = db.Column(db.Float, default=0.0)
    saturday_to_be_ordered = db.Column(db.Float, default=0.0)
    saturday_ordered_received = db.Column(db.Float, default=0.0)
    saturday_consumed_kg = db.Column(db.Float, default=0.0)
    saturday_closing_stock = db.Column(db.Float, default=0.0)

    sunday_opening_stock = db.Column(db.Float, default=0.0)
    sunday_required_kg = db.Column(db.Float, default=0.0)
    sunday_variance = db.Column(db.Float, default=0.0)
    sunday_to_be_ordered = db.Column(db.Float, default=0.0)
    sunday_ordered_received = db.Column(db.Float, default=0.0)
    sunday_consumed_kg = db.Column(db.Float, default=0.0)
    sunday_closing_stock = db.Column(db.Float, default=0.0)

    # Relationship to ItemMaster
    item = db.relationship('ItemMaster', backref='inventories')
    
    def __repr__(self):
        return f'<Inventory {self.item.item_code} - Week {self.week_commencing}>'