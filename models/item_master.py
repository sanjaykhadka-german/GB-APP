from database import db
from sqlalchemy.orm import relationship

class ItemMaster(db.Model):
    """
    Central table for all items in the system.
    Contains self-referencing relationships for FG composition.
    """
    __tablename__ = 'item_master'

    id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255), nullable=False)
    
    # Foreign Key to the ItemType lookup table
    item_type_id = db.Column(db.Integer, db.ForeignKey('item_type.id'), nullable=False)
    
    category = db.Column(db.String(100))
    department = db.Column(db.String(100))
    machinery = db.Column(db.String(100))
    min_stock = db.Column(db.DECIMAL(10, 2), default=0.00)
    max_stock = db.Column(db.DECIMAL(10, 2), default=0.00)
    is_active = db.Column(db.Boolean, default=True)
    price_per_kg = db.Column(db.DECIMAL(12, 4), nullable=True)
    is_make_to_order = db.Column(db.Boolean, default=False)
    loss_percentage = db.Column(db.DECIMAL(5, 2), default=0.00)
    calculation_factor = db.Column(db.DECIMAL(10, 4), default=1.0000)

    # --- Relationships ---

    # Link to the ItemType object
    item_type = relationship("ItemType", back_populates="items")

    # --- FG Composition (Self-referencing Foreign Keys) ---
    # These will only be populated for Finished Goods (FG)
    wip_item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=True)
    wipf_item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=True)
    
    # These relationships allow an FG to easily access its WIP and WIPF components
    # We specify foreign_keys to resolve ambiguity for SQLAlchemy
    wip_component = relationship("ItemMaster", foreign_keys=[wip_item_id])
    wipf_component = relationship("ItemMaster", foreign_keys=[wipf_item_id])
    
    # --- Recipe Relationships ---
    
    # If this item is a WIP, this relationship gives a list of its recipe components
    # It links to all RecipeMaster entries where this item is the 'recipe_wip'
    components = relationship(
        'RecipeMaster', 
        foreign_keys='RecipeMaster.recipe_wip_id', 
        back_populates='recipe_wip', 
        cascade="all, delete-orphan"
    )

    # If this item is used as a component (RM or WIP), this relationship shows all the recipes it is used in
    # It links to all RecipeMaster entries where this item is a 'component_item'
    used_in_recipes = relationship(
        'RecipeMaster', 
        foreign_keys='RecipeMaster.component_item_id'
        # Note: Removed back_populates since component_item doesn't have it
    )

    def __repr__(self):
        return f"<ItemMaster {self.item_code} ({self.description})>"


class ItemAllergen(db.Model):
    __tablename__ = 'item_allergen'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)
    allergen_id = db.Column(db.Integer, db.ForeignKey('allergen.allergens_id'), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('item_id', 'allergen_id', name='uix_item_allergen'),
    )
    