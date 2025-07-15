from app import db
from sqlalchemy.orm import relationship
from datetime import datetime

class ItemType(db.Model):
    """Item type lookup table (RM, WIP, WIPF, FG, PKG)"""
    __tablename__ = 'item_type'
    
    id = db.Column(db.Integer, primary_key=True)
    type_name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship
    items = relationship("ItemMaster", back_populates="item_type")
    
    def __repr__(self):
        return f"<ItemType {self.type_name}>"

class Category(db.Model):
    """Category lookup table"""
    __tablename__ = 'category'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=True)
    
    def __repr__(self):
        return f"<Category {self.name}>"

class Department(db.Model):
    """Department lookup table"""
    __tablename__ = 'department'
    
    department_id = db.Column(db.Integer, primary_key=True)
    departmentName = db.Column(db.String(50), nullable=False, unique=True)
    
    def __repr__(self):
        return f"<Department {self.departmentName}>"

class UOM(db.Model):
    """Unit of Measure lookup table"""
    __tablename__ = 'uom_type'
    
    UOMID = db.Column(db.Integer, primary_key=True)
    uom_name = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(100), nullable=True)
    
    def __repr__(self):
        return f"<UOM {self.uom_name}>"

class ItemMaster(db.Model):
    """
    Central table for all items in the system.
    Uses composite unique constraint on (item_code, description) to allow
    multiple variants of the same item code with different descriptions.
    """
    __tablename__ = 'item_master'

    id = db.Column(db.Integer, primary_key=True)
    # Note: NO unique=True on item_code alone
    item_code = db.Column(db.String(50), nullable=False, index=True)
    description = db.Column(db.String(255), nullable=False)
    
    # Foreign Key to the ItemType lookup table
    item_type_id = db.Column(db.Integer, db.ForeignKey('item_type.id'), nullable=False)
    
    # Foreign keys for lookup tables
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.department_id'), nullable=True)
    uom_id = db.Column(db.Integer, db.ForeignKey('uom_type.UOMID'), nullable=True)
    
    # Item properties
    min_stock = db.Column(db.DECIMAL(10, 2), default=0.00)
    max_stock = db.Column(db.DECIMAL(10, 2), default=0.00)
    is_active = db.Column(db.Boolean, default=True)
    price_per_kg = db.Column(db.DECIMAL(12, 4), nullable=True)
    price_per_uom = db.Column(db.DECIMAL(12, 4), nullable=True)
    is_make_to_order = db.Column(db.Boolean, default=False)
    loss_percentage = db.Column(db.DECIMAL(5, 2), default=0.00)
    calculation_factor = db.Column(db.DECIMAL(10, 4), default=1.0000)
    
    # Additional properties
    min_level = db.Column(db.DECIMAL(10, 2), nullable=True)
    max_level = db.Column(db.DECIMAL(10, 2), nullable=True)
    kg_per_unit = db.Column(db.DECIMAL(10, 4), nullable=True)
    units_per_bag = db.Column(db.DECIMAL(10, 2), nullable=True)
    avg_weight_per_unit = db.Column(db.DECIMAL(10, 4), nullable=True)
    supplier_name = db.Column(db.String(255), nullable=True)

    # Audit fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- FG Composition (Self-referencing Foreign Keys) ---
    wip_item_id = db.Column(db.Integer, db.ForeignKey('item_master.id', ondelete='SET NULL'), nullable=True)
    wipf_item_id = db.Column(db.Integer, db.ForeignKey('item_master.id', ondelete='SET NULL'), nullable=True)

    # --- COMPOSITE UNIQUE CONSTRAINT ---
    __table_args__ = (
        db.UniqueConstraint('item_code', 'description', name='uq_item_code_description'),
    )

    # --- Relationships ---

    # Link to the ItemType object
    item_type = relationship("ItemType", back_populates="items")
    
    # Lookup table relationships
    category = relationship("Category", foreign_keys=[category_id])
    department = relationship("Department", foreign_keys=[department_id])
    uom = relationship("UOM", foreign_keys=[uom_id])
    
    # Self-referencing relationships for FG composition
    wip_item = relationship("ItemMaster", foreign_keys=[wip_item_id], remote_side=[id], 
                           backref=db.backref('wip_used_by', lazy='dynamic'))
    wipf_item = relationship("ItemMaster", foreign_keys=[wipf_item_id], remote_side=[id], 
                            backref=db.backref('wipf_used_by', lazy='dynamic'))
    
    # Recipe relationships
    components = relationship('RecipeMaster', foreign_keys='RecipeMaster.recipe_wip_id', 
                             back_populates='recipe_wip', cascade="all, delete-orphan")
    used_in_recipes = relationship('RecipeMaster', foreign_keys='RecipeMaster.component_item_id',
                                  back_populates='component_item')

    def __repr__(self):
        return f"<ItemMaster {self.item_code} ({self.description})>"
    
    def to_dict(self):
        """Convert item to dictionary for JSON responses"""
        return {
            'id': self.id,
            'item_code': self.item_code,
            'description': self.description,
            'item_type': self.item_type.type_name if self.item_type else None,
            'category': self.category.name if self.category else None,
            'department': self.department.departmentName if self.department else None,
            'uom': self.uom.uom_name if self.uom else None,
            'min_stock': float(self.min_stock) if self.min_stock else 0,
            'max_stock': float(self.max_stock) if self.max_stock else 0,
            'is_active': self.is_active,
            'price_per_kg': float(self.price_per_kg) if self.price_per_kg else None,
            'price_per_uom': float(self.price_per_uom) if self.price_per_uom else None,
            'is_make_to_order': self.is_make_to_order,
            'loss_percentage': float(self.loss_percentage) if self.loss_percentage else 0,
            'calculation_factor': float(self.calculation_factor) if self.calculation_factor else 1,
            'wip_item_code': self.wip_item.item_code if self.wip_item else None,
            'wipf_item_code': self.wipf_item.item_code if self.wipf_item else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def find_by_code_and_description(cls, item_code, description):
        """Find item by exact item_code and description match"""
        return cls.query.filter_by(item_code=item_code, description=description).first()
    
    @classmethod
    def find_variants_by_code(cls, item_code):
        """Find all variants of an item by item_code"""
        return cls.query.filter_by(item_code=item_code).all()
    
    @classmethod
    def search_items(cls, search_term, limit=50):
        """Search items by code or description"""
        if not search_term:
            return cls.query.limit(limit).all()
        
        search_pattern = f"%{search_term}%"
        return cls.query.filter(
            db.or_(
                cls.item_code.like(search_pattern),
                cls.description.like(search_pattern)
            )
        ).limit(limit).all()