from database import db

class ItemMaster(db.Model):
    __tablename__ = 'item_master'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_code = db.Column(db.String(20), unique=True, nullable=False)  # e.g., RM001, 2006, 2006.56, 2006.1
    description = db.Column(db.String(255))
    
    # Foreign key to ItemType table
    item_type_id = db.Column(db.Integer, db.ForeignKey('item_type.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.department_id'), nullable=True)
    machinery_id = db.Column(db.Integer, db.ForeignKey('machinery.machineID', ondelete='SET NULL'), nullable=True)
    uom_id = db.Column(db.Integer, db.ForeignKey('uom_type.UOMID'), nullable=True)  # Unit of Measure (kg, unit, box)
    
    # Item Attributes (previously scattered, now centralized)
    min_level = db.Column(db.Float)
    max_level = db.Column(db.Float)
    price_per_kg = db.Column(db.Float)  # For raw materials
    price_per_uom = db.Column(db.Float)  # Price per unit of measure
    kg_per_unit = db.Column(db.Float)   # For WIPF/FG
    units_per_bag = db.Column(db.Float)  # For FG
    avg_weight_per_unit = db.Column(db.Float)  # Average weight per unit in kg
    loss_percentage = db.Column(db.Float)  # Production/Filling loss
    supplier_name = db.Column(db.String(255))  # Name of the supplier for this item
    is_make_to_order = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    fw = db.Column(db.Boolean, default=False) 
    calculation_factor = db.Column(db.Float) 
    
    # User tracking fields
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Relationships
    item_type = db.relationship('ItemType', backref='items')
    category = db.relationship('Category', backref='items')
    department = db.relationship('Department', backref='items')
    machinery = db.relationship('Machinery', backref='items')
    uom = db.relationship('UOM', backref='items')
    allergens = db.relationship('Allergen', secondary='item_allergen', backref='items')

    # Recipe relationships
    recipes_where_raw_material = db.relationship('RecipeMaster', 
                                               foreign_keys='RecipeMaster.raw_material_id',
                                               primaryjoin='ItemMaster.id == RecipeMaster.raw_material_id')
    
    recipes_where_finished_good = db.relationship('RecipeMaster',
                                                foreign_keys='RecipeMaster.finished_good_id',
                                                primaryjoin='ItemMaster.id == RecipeMaster.finished_good_id')

    def __repr__(self):
        return f'<ItemMaster {self.item_code} - {self.description}>'
    
    @property
    def is_raw_material(self):
        return self.item_type and self.item_type.type_name == 'RM'

    @property 
    def is_wip(self):
        return self.item_type and self.item_type.type_name == 'WIP'
        
    @property
    def is_wipf(self):
        return self.item_type and self.item_type.type_name == 'WIPF'
        
    @property
    def is_finished_good(self):
        return self.item_type and self.item_type.type_name == 'FG'

    def get_recipe_components(self):
        """Get all raw materials used in recipes for this item."""
        return [recipe.raw_material_item for recipe in self.recipes_where_finished_good]

    def get_recipes_using_this_item(self):
        """Get all recipes where this item is used as a raw material/component."""
        return [recipe.finished_good_item for recipe in self.recipes_where_raw_material]
    
    def get_raw_material_components(self):
        """Get all Raw Material components used in recipes for this item"""
        components = []
        for recipe in self.recipes_where_finished_good:
            if recipe.raw_material_item and recipe.raw_material_item.is_raw_material:
                components.append(recipe.raw_material_item)
        return components

    def get_wip_components(self):
        """Get all WIP (Work In Progress) components used in recipes for this item"""
        components = []
        for recipe in self.recipes_where_finished_good:
            if recipe.raw_material_item and recipe.raw_material_item.is_wip:
                components.append(recipe.raw_material_item)
        return components

    def get_wipf_components(self):
        """Get all WIPF (Work In Progress - Filling) components used in recipes for this item"""
        components = []
        for recipe in self.recipes_where_finished_good:
            if recipe.raw_material_item and recipe.raw_material_item.is_wipf:
                components.append(recipe.raw_material_item)
        return components

    def get_all_components_by_type(self):
        """Get all components categorized by type (RM, WIP, WIPF)"""
        return {
            'raw_materials': self.get_raw_material_components(),
            'wip': self.get_wip_components(),
            'wipf': self.get_wipf_components()
        }

    def get_component_summary(self):
        """Get a summary of component counts by type"""
        components = self.get_all_components_by_type()
        return {
            'raw_material_count': len(components['raw_materials']),
            'wip_count': len(components['wip']),
            'wipf_count': len(components['wipf']),
            'total_components': len(components['raw_materials']) + len(components['wip']) + len(components['wipf'])
        }

    def get_production_flow_type(self):
        """Determine the production flow type based on components"""
        if not self.is_finished_good:
            return "Not a finished good"
        
        summary = self.get_component_summary()
        
        if summary['total_components'] == 0:
            return "No recipe defined"
        elif summary['wip_count'] > 0 and summary['wipf_count'] > 0:
            return "Complex flow (RM → WIP → WIPF → FG)"
        elif summary['wip_count'] > 0:
            return "Production flow (RM → WIP → FG)"
        elif summary['wipf_count'] > 0:
            return "Filling flow (RM → WIPF → FG)"
        else:
            return "Direct production (RM → FG)"

    def get_manufacturing_hierarchy(self):
        """Get the complete manufacturing hierarchy for this item"""
        hierarchy = {
            'item': self,
            'flow_type': self.get_production_flow_type(),
            'components_by_type': self.get_all_components_by_type(),
            'summary': self.get_component_summary()
        }
        return hierarchy

    # NEW: Enhanced BOM explosion methods
    def get_components_recursive(self, processed_items=None):
        """Get all components needed recursively (supports multi-level BOM)"""
        if processed_items is None:
            processed_items = set()
        
        if self.id in processed_items:
            return []  # Prevent circular references
        
        processed_items.add(self.id)
        all_components = []
        
        # Get direct components
        direct_components = self.get_all_components_by_type()
        
        # Add direct components
        for component_type, components in direct_components.items():
            for comp_data in components:
                all_components.append({
                    'item': comp_data['item'],
                    'level': 1,
                    'type': component_type,
                    'kg_per_batch': comp_data['kg_per_batch'],
                    'percentage': comp_data['percentage']
                })
                
                # Recursively get components of components
                sub_components = comp_data['item'].get_components_recursive(processed_items.copy())
                for sub_comp in sub_components:
                    sub_comp['level'] += 1
                    all_components.append(sub_comp)
        
        return all_components

    def calculate_total_requirements(self, required_kg):
        """Calculate total requirements for all components to make required_kg of this item"""
        requirements = {}
        components = self.get_components_recursive()
        
        for comp in components:
            item_code = comp['item'].item_code
            if item_code not in requirements:
                requirements[item_code] = {
                    'item': comp['item'],
                    'total_kg': 0,
                    'type': comp['type'],
                    'levels': []
                }
            
            # Calculate requirement based on recipe
            comp_requirement = required_kg * (comp['kg_per_batch'] or comp['percentage'] or 0)
            requirements[item_code]['total_kg'] += comp_requirement
            requirements[item_code]['levels'].append(comp['level'])
        
        return requirements

    def get_downstream_items(self):
        """Get all items that use this item as a component (what this feeds into)"""
        downstream = []
        for recipe in self.recipes_where_raw_material:
            if recipe.finished_good_item:
                downstream.append({
                    'item': recipe.finished_good_item,
                    'recipe': recipe,
                    'kg_per_batch': recipe.kg_per_batch,
                    'percentage': recipe.percentage
                })
        return downstream

class ItemAllergen(db.Model):
    __tablename__ = 'item_allergen'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)
    allergen_id = db.Column(db.Integer, db.ForeignKey('allergen.allergens_id'), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('item_id', 'allergen_id', name='uix_item_allergen'),
    )
    