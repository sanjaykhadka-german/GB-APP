from app import db
from sqlalchemy.orm import relationship
from datetime import datetime

class RecipeMaster(db.Model):
    """
    Recipe/BOM table that links WIP items to their component items (RM or other WIP).
    Each record represents one component in a recipe.
    """
    __tablename__ = 'recipe_master'

    id = db.Column(db.Integer, primary_key=True)
    
    # WIP item that this recipe is for
    recipe_wip_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)
    
    # Component item (RM or WIP) used in this recipe
    component_item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)
    
    # Quantity of component needed per batch
    quantity_kg = db.Column(db.DECIMAL(10, 3), nullable=False)
    
    # Percentage of total recipe (optional, for reporting)
    percentage = db.Column(db.DECIMAL(5, 2), nullable=True)
    
    # Sequence order for recipe steps
    sequence_number = db.Column(db.Integer, default=1)
    
    # Additional recipe properties
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Audit fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint to prevent duplicate components in same recipe
    __table_args__ = (
        db.UniqueConstraint('recipe_wip_id', 'component_item_id', name='uq_recipe_component'),
    )

    # --- Relationships ---
    
    # Link to the WIP item this recipe belongs to
    recipe_wip = relationship("ItemMaster", foreign_keys=[recipe_wip_id], 
                             back_populates="components")
    
    # Link to the component item used in this recipe
    component_item = relationship("ItemMaster", foreign_keys=[component_item_id], 
                                 back_populates="used_in_recipes")

    def __repr__(self):
        return f"<RecipeMaster WIP:{self.recipe_wip_id} Component:{self.component_item_id} Qty:{self.quantity_kg}>"
    
    def to_dict(self):
        """Convert recipe component to dictionary for JSON responses"""
        return {
            'id': self.id,
            'recipe_wip_id': self.recipe_wip_id,
            'recipe_wip_code': self.recipe_wip.item_code if self.recipe_wip else None,
            'recipe_wip_description': self.recipe_wip.description if self.recipe_wip else None,
            'component_item_id': self.component_item_id,
            'component_code': self.component_item.item_code if self.component_item else None,
            'component_description': self.component_item.description if self.component_item else None,
            'component_type': self.component_item.item_type.type_name if self.component_item and self.component_item.item_type else None,
            'quantity_kg': float(self.quantity_kg) if self.quantity_kg else 0,
            'percentage': float(self.percentage) if self.percentage else None,
            'sequence_number': self.sequence_number,
            'is_active': self.is_active,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_recipe_components(cls, wip_item_id):
        """Get all components for a specific WIP item recipe"""
        return cls.query.filter_by(
            recipe_wip_id=wip_item_id, 
            is_active=True
        ).order_by(cls.sequence_number).all()
    
    @classmethod
    def get_component_usage(cls, component_item_id):
        """Get all recipes that use a specific component"""
        return cls.query.filter_by(
            component_item_id=component_item_id, 
            is_active=True
        ).all()
    
    @classmethod
    def calculate_total_recipe_weight(cls, wip_item_id):
        """Calculate total weight of all components in a recipe"""
        total = db.session.query(db.func.sum(cls.quantity_kg)).filter_by(
            recipe_wip_id=wip_item_id, 
            is_active=True
        ).scalar()
        return float(total) if total else 0.0
    
    def calculate_percentage(self):
        """Calculate and update percentage for this component"""
        total_weight = self.calculate_total_recipe_weight(self.recipe_wip_id)
        if total_weight > 0:
            self.percentage = (float(self.quantity_kg) / total_weight) * 100
        else:
            self.percentage = 0
        return self.percentage