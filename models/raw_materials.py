from database import db

class RawMaterials(db.Model):
    __tablename__ = 'raw_materials'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    raw_material_code = db.Column(db.String(20), unique=True, nullable=False)  # e.g., RM001
    raw_material = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    department_id = db.Column(db.Integer, db.ForeignKey('department.department_id'))
    uom_id = db.Column(db.Integer, db.ForeignKey('uom_type.UOMID'))
    min_level = db.Column(db.Float)
    max_level = db.Column(db.Float)
    price_per_kg = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Relationships
    category = db.relationship('Category', backref='raw_materials')
    department = db.relationship('Department', backref='raw_materials')
    uom = db.relationship('UOM', backref='raw_materials')

    def __repr__(self):
        return f'<RawMaterial {self.raw_material_code} - {self.raw_material}>' 