# models/inventory.py
from database import db
from datetime import datetime
from models.category import Category
from models.item_master import ItemMaster

class Inventory(db.Model):
    __tablename__ = 'inventory'

    id = db.Column(db.Integer, primary_key=True)
    week_commencing = db.Column(db.Date, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    raw_material_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)
    price_per_kg = db.Column(db.Float, nullable=False)
    
    # New columns based on user requirements
    required_total_production = db.Column(db.Float, default=0.0)  # C1/C2: Required in TOTAL for production
    value_required_rm = db.Column(db.Float, default=0.0)  # F1/F2: $ Value for Required RM
    current_stock = db.Column(db.Float, default=0.0)  # G1/G2: SOH from raw_material_stocktake
    supplier_name = db.Column(db.String(255), nullable=True)  # H1/H2: Supplier Name
    required_for_plan = db.Column(db.Float, default=0.0)  # I1/I2: Required for plan
    variance_week = db.Column(db.Float, default=0.0)  # J1/J2: Variance for the week
    kg_required = db.Column(db.Float, default=0.0)  # K1/K2: KG Required
    variance = db.Column(db.Float, default=0.0)  # L1/L2: Variance
    to_be_ordered = db.Column(db.Float, default=0.0)  # M1/M2: To Be Ordered
    closing_stock = db.Column(db.Float, default=0.0)  # N1/N2: Closing Stock
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    category = db.relationship('Category', backref='inventories')
    raw_material = db.relationship('ItemMaster', backref='inventories')

    @property
    def value_soh(self):
        """Calculate SOH value: current_stock * price_per_kg"""
        return self.current_stock * self.price_per_kg

    @property
    def calculated_value_required_rm(self):
        """Calculate $ Value for Required RM: required_total_production * price_per_kg"""
        return self.required_total_production * self.price_per_kg

    @property
    def calculated_variance_week(self):
        """Calculate Variance for the week: IFERROR(current_stock - required_for_plan, "")"""
        try:
            return self.current_stock - self.required_for_plan
        except:
            return 0.0

    @property
    def calculated_variance(self):
        """Calculate Variance: IFERROR(current_stock - kg_required, "")"""
        try:
            return self.current_stock - self.kg_required
        except:
            return 0.0