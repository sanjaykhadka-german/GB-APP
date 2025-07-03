from database import db
from sqlalchemy.orm import relationship

class RecipeMaster(db.Model):
    """
    Association table defining the Bill of Materials for a WIP item.
    Links a WIP item (recipe_wip) to its component items (which can be RM or other WIP items).
    """
    __tablename__ = 'recipe_master'

    id = db.Column(db.Integer, primary_key=True)
    quantity_kg = db.Column(db.DECIMAL(10, 4), nullable=False)

    # Foreign key to the WIP item being defined
    recipe_wip_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)
    
    # RENAMED for clarity: This component can be an RM or another WIP
    component_item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)

    # --- Relationships ---

    # Links back to the ItemMaster object that represents the WIP recipe
    recipe_wip = relationship(
        'ItemMaster', 
        foreign_keys=[recipe_wip_id], 
        back_populates='components'
    )
    
    # RENAMED relationship link for clarity
    component_item = relationship(
        'ItemMaster', 
        foreign_keys=[component_item_id]
        # Note: The 'used_in_recipes' back_populates might need adjustment
        # if you rename it on the ItemMaster side as well.
    )

    # Ensure a component can only be added once to a specific recipe
    __table_args__ = (
        db.UniqueConstraint('recipe_wip_id', 'component_item_id', name='uq_recipe_component'),
    )

    def __repr__(self):
        return f"<RecipeMaster {self.recipe_wip.item_code} uses {self.quantity_kg}kg of {self.component_item.item_code}>"