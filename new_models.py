from database import db
from sqlalchemy import CheckConstraint

class ItemMaster(db.Model):
    __tablename__ = 'item_master'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.String(255))
    
    # Direct item type (simplified)
    item_type = db.Column(db.String(20), nullable=False)
    
    # Basic attributes
    category = db.Column(db.String(100))
    department = db.Column(db.String(100))
    machinery = db.Column(db.String(100))
    min_stock = db.Column(db.Float)
    max_stock = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True)
    price_per_kg = db.Column(db.Float)
    is_make_to_order = db.Column(db.Boolean, default=False)
    loss_percentage = db.Column(db.Float)
    calculation_factor = db.Column(db.Float)
    
    # Self-referencing FKs for FG composition
    wip_item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=True)
    wipf_item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=True)
    
    # Relationships
    wip_item = db.relationship('ItemMaster', remote_side=[id], foreign_keys=[wip_item_id])
    wipf_item = db.relationship('ItemMaster', remote_side=[id], foreign_keys=[wipf_item_id])

class RecipeComponent(db.Model):
    __tablename__ = 'recipe_components'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    wip_item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)
    rm_item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)
    quantity_kg = db.Column(db.Float, nullable=False)
    recipe_code = db.Column(db.String(50))
    step_order = db.Column(db.Integer, default=1)
    
    # Relationships
    wip_item = db.relationship('ItemMaster', foreign_keys=[wip_item_id])
    rm_item = db.relationship('ItemMaster', foreign_keys=[rm_item_id]) 