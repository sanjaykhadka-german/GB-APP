from database import db
from sqlalchemy import event

class RecipeMaster(db.Model):
    __tablename__ = 'recipe_master'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    recipe_code = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    raw_material_id = db.Column(db.Integer, db.ForeignKey('item_master.id', ondelete='CASCADE'), nullable=False)
    finished_good_id = db.Column(db.Integer, db.ForeignKey('item_master.id', ondelete='CASCADE'), nullable=False)
    kg_per_batch = db.Column(db.Float)
    percentage = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Relationships
    raw_material = db.relationship('ItemMaster', foreign_keys=[raw_material_id], backref='recipes_as_raw_material')
    finished_good = db.relationship('ItemMaster', foreign_keys=[finished_good_id], backref='recipes_as_finished_good')

    def __repr__(self):
        return f'<RecipeMaster {self.recipe_code}>'

# Add validation before insert or update
# Temporarily commenting out validation to debug add/edit issues
# @event.listens_for(RecipeMaster, 'before_insert')
# @event.listens_for(RecipeMaster, 'before_update')
# def validate_item_types(mapper, connection, target):
#     from models.item_master import ItemMaster  # Import here to avoid circular import
#     
#     # Check raw material type
#     raw_material = db.session.get(ItemMaster, target.raw_material_id)
#     if not raw_material or raw_material.item_type != 'raw_material':
#         raise ValueError("raw_material_id must reference an item of type 'raw_material'")
#     
#     # Check finished good type
#     finished_good = db.session.get(ItemMaster, target.finished_good_id)
#     if not finished_good or finished_good.item_type != 'finished_good':
#         raise ValueError("finished_good_id must reference an item of type 'finished_good'")