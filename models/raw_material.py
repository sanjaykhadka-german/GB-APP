# from database import db
# from datetime import date

# class RawMaterial(db.Model):
#     __tablename__ = 'raw_material'

#     # Primary key
#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)

#     # Core attributes
#     material_code = db.Column(db.String(50), nullable=False, unique=True)
#     description = db.Column(db.String(255), nullable=False)

#     # Foreign keys for categorization and measurement
#     category_id = db.Column(db.Integer, db.ForeignKey('category.categoryID'), nullable=True)
#     UOMID = db.Column(db.Integer, db.ForeignKey('uom_type.UOMID'), nullable=True)
#     department_id = db.Column(db.Integer, db.ForeignKey('department.department_id'), nullable=True)
#     item_type_id = db.Column(db.Integer, db.ForeignKey('item_type.itemTypeID'), nullable=True)

#     # Additional attributes (optional, based on your needs)
#     stock_quantity = db.Column(db.Float, default=0.0)  # Current stock level
#     reorder_level = db.Column(db.Float, default=0.0)   # Threshold for reordering
#     cost_per_unit = db.Column(db.Float, default=0.0)   # Cost per unit for inventory tracking

#     # Relationships
#     category = db.relationship('Category', backref='raw_materials')
#     uom = db.relationship('UOM', backref='raw_materials')
#     department = db.relationship('Department', backref='raw_materials')
#     item_type = db.relationship('ItemType', backref='raw_materials')

#     def __repr__(self):
#         return f"<RawMaterial {self.material_code} - {self.description}>"

from database import db
from datetime import datetime

class RawMaterial(db.Model):
    __tablename__ = 'raw_material'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    production_date = db.Column(db.Date, nullable=False)
    week_commencing = db.Column(db.Date)
    raw_material = db.Column(db.String(255), nullable=False)
    meat_required = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)