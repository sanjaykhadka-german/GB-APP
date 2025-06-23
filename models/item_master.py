from database import db

class ItemMaster(db.Model):
    __tablename__ = 'item_master'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_code = db.Column(db.String(50), unique=True, nullable=False)  # Can be FG, WIPF, WIP codes
    description = db.Column(db.String(255))
    item_type = db.Column(db.String(20), nullable=False)  # 'Raw Material', 'Finished Good', 'WIPF', 'WIP'
    category_id = db.Column(db.Integer, db.ForeignKey('category.id', ondelete='SET NULL'), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.department_id', ondelete='SET NULL'), nullable=True)
    machinery_id = db.Column(db.Integer, db.ForeignKey('machinery.machineID', ondelete='SET NULL'), nullable=True)
    uom_id = db.Column(db.Integer, db.ForeignKey('uom_type.UOMID', ondelete='SET NULL'), nullable=True)
    
    # Common fields for all types
    min_level = db.Column(db.Float)
    max_level = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True)
    
    # Raw Material specific fields
    price_per_kg = db.Column(db.Float)
    
    # Finished Good/WIP/WIPF specific fields
    is_make_to_order = db.Column(db.Boolean, default=False)
    kg_per_unit = db.Column(db.Float)
    units_per_bag = db.Column(db.Float)
    loss_percentage = db.Column(db.Float)  # Previously 'loss' in joining
    
    # Additional fields from joining table
    fw = db.Column(db.Boolean, default=False)  # FW flag from joining
    weekly_average = db.Column(db.Float)  # Weekly average from joining
    product_description = db.Column(db.String(255))  # Additional description for products
    
    # Cross-reference fields for migration period (will be removed later)
    filling_code = db.Column(db.String(50))  # Reference to WIPF items
    production_code = db.Column(db.String(50))  # Reference to WIP items
    
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Relationships
    category = db.relationship('Category', backref='items')
    department = db.relationship('Department', backref='items')
    machinery = db.relationship('Machinery', backref='items')
    uom = db.relationship('UOM', backref='items')
    allergens = db.relationship('Allergen', secondary='item_allergen', backref='items')

    def __repr__(self):
        return f'<ItemMaster {self.item_code} - {self.description}>'
    
class ItemAllergen(db.Model):
    __tablename__ = 'item_allergen'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)
    allergen_id = db.Column(db.Integer, db.ForeignKey('allergen.allergens_id'), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('item_id', 'allergen_id', name='uix_item_allergen'),
    )
    