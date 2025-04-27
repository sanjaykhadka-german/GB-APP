from database import db

class RecipeMaster(db.Model):
    __tablename__ = 'recipe_master'
    finished_product_id = db.Column(db.String(255), db.ForeignKey('item_master.itemID'), primary_key=True)
    raw_material_id = db.Column(db.String(255), db.ForeignKey('item_master.itemID'), primary_key=True)
    recipeName = db.Column(db.String(255), nullable=False)
    usageMaterial = db.Column(db.Numeric(20, 3), nullable=False)
    uom = db.Column(db.String(50), nullable=False)
    percentage = db.Column(db.Numeric(5, 3))
    finished_product = db.relationship('ItemMaster', foreign_keys=[finished_product_id], backref='recipes_as_product')
    raw_material = db.relationship('ItemMaster', foreign_keys=[raw_material_id], backref='recipes_as_material')