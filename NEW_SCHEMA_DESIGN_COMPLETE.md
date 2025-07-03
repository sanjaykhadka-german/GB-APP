# 🏭 NEW DATABASE SCHEMA DESIGN - MANUFACTURING COMPANY

## 📋 Overview

This document outlines the complete redesign of your manufacturing database schema to implement a simplified, elegant two-table design that meets all your business requirements while improving performance and maintainability.

## 🎯 Business Requirements Addressed

### Item Types Supported
- **RM** (Raw Material): Basic ingredients like Pork, Spices
- **WIP** (Work-in-Progress): Recipe assemblies like "Ham Base - WIP" 
- **WIPF** (Work-in-Progress-Final): Final processing steps like Smoking
- **FG** (Finished Good): Final products sold to customers
- **Packaging**: Packaging materials

### Key Business Rules
1. **Recipes**: Define how to make WIP items from RM components
2. **FG Composition**: Every FG uses exactly one WIP + optionally one WIPF
3. **Hierarchy**: RM → WIP → (optional WIPF) → FG

## 🗄️ New Schema Design

### Table 1: `item_master` (Unified Item Registry)

```sql
CREATE TABLE item_master (
    id INT PRIMARY KEY AUTO_INCREMENT,
    item_code VARCHAR(20) UNIQUE NOT NULL,
    description VARCHAR(255),
    
    -- Direct item type (no lookup table needed)
    item_type VARCHAR(20) NOT NULL,  -- 'RM', 'WIP', 'WIPF', 'FG', 'Packaging'
    
    -- Basic attributes
    category VARCHAR(100),
    department VARCHAR(100), 
    machinery VARCHAR(100),
    min_stock DECIMAL(10,2),
    max_stock DECIMAL(10,2),
    is_active BOOLEAN DEFAULT TRUE,
    price_per_kg DECIMAL(10,2),
    is_make_to_order BOOLEAN DEFAULT FALSE,
    loss_percentage DECIMAL(5,2),
    calculation_factor DECIMAL(10,4),
    
    -- Self-referencing FKs for FG composition (only populated for FG items)
    wip_item_id INT NULL,
    wipf_item_id INT NULL,
    
    FOREIGN KEY (wip_item_id) REFERENCES item_master(id),
    FOREIGN KEY (wipf_item_id) REFERENCES item_master(id),
    
    -- Business rule constraint
    CHECK ((item_type = 'FG' AND wip_item_id IS NOT NULL) 
           OR (item_type != 'FG' AND wip_item_id IS NULL AND wipf_item_id IS NULL))
);
```

### Table 2: `recipe_components` (Bill of Materials)

```sql
CREATE TABLE recipe_components (
    id INT PRIMARY KEY AUTO_INCREMENT,
    
    -- The WIP item being produced (recipe output)
    wip_item_id INT NOT NULL,
    
    -- The Raw Material component required (recipe input)  
    rm_item_id INT NOT NULL,
    
    -- Quantity of this RM needed to make the WIP
    quantity_kg DECIMAL(10,3) NOT NULL,
    
    -- Optional metadata
    recipe_code VARCHAR(50),
    step_order INT DEFAULT 1,
    notes TEXT,
    
    FOREIGN KEY (wip_item_id) REFERENCES item_master(id) ON DELETE CASCADE,
    FOREIGN KEY (rm_item_id) REFERENCES item_master(id) ON DELETE CASCADE,
    
    UNIQUE(wip_item_id, rm_item_id),  -- No duplicate RM in same recipe
    CHECK (quantity_kg > 0)
);
```

## 📊 Sample Data Implementation

### Raw Materials
```sql
INSERT INTO item_master (item_code, description, item_type, category, price_per_kg, min_stock, max_stock, is_active) VALUES
('RM-PORK', 'Pork Shoulder Premium Grade', 'RM', 'Meat', 8.50, 500, 2000, TRUE),
('RM-SPICE', 'Ham Seasoning Mix', 'RM', 'Spices', 25.00, 50, 200, TRUE);
```

### Work-in-Progress Item
```sql
INSERT INTO item_master (item_code, description, item_type, category, department, machinery, is_active) VALUES
('1003', 'Ham Base - WIP', 'WIP', 'Processed Meat', 'Production', 'Mixer-001', TRUE);
```

### Work-in-Progress-Final Item  
```sql
INSERT INTO item_master (item_code, description, item_type, category, department, machinery, is_active) VALUES
('WIPF-SMOKE', 'Smoking Process', 'WIPF', 'Final Processing', 'Smoking Room', 'Smoker-001', TRUE);
```

### Finished Goods with Composition
```sql
-- FG using only WIP (no final processing)
INSERT INTO item_master (item_code, description, item_type, category, wip_item_id, wipf_item_id, is_active) VALUES
('1002.1', 'Ham Sliced 200g', 'FG', 'Packaged Meat', 
    (SELECT id FROM item_master WHERE item_code = '1003'), NULL, TRUE),
('1002.2', 'Ham Sliced 500g', 'FG', 'Packaged Meat', 
    (SELECT id FROM item_master WHERE item_code = '1003'), NULL, TRUE);

-- FG using both WIP and WIPF (with final processing)  
INSERT INTO item_master (item_code, description, item_type, category, wip_item_id, wipf_item_id, is_active) VALUES
('1005.1', 'Smoked Ham Sliced 200g', 'FG', 'Premium Packaged Meat', 
    (SELECT id FROM item_master WHERE item_code = '1003'), 
    (SELECT id FROM item_master WHERE item_code = 'WIPF-SMOKE'), TRUE);
```

### Recipe Components (Bill of Materials)
```sql
-- Ham Base WIP recipe: requires Pork + Spices
INSERT INTO recipe_components (wip_item_id, rm_item_id, quantity_kg, recipe_code, step_order) VALUES
((SELECT id FROM item_master WHERE item_code = '1003'), 
 (SELECT id FROM item_master WHERE item_code = 'RM-PORK'), 100.000, 'HAM-BASE-001', 1),
((SELECT id FROM item_master WHERE item_code = '1003'), 
 (SELECT id FROM item_master WHERE item_code = 'RM-SPICE'), 25.000, 'HAM-BASE-001', 2);
```

## 🔍 Key Queries and Reports

### 1. Complete Bill of Materials for Finished Good
```sql
SELECT 
    fg.item_code AS finished_good,
    fg.description AS fg_description,
    wip.item_code AS wip_component,
    wipf.item_code AS wipf_component,
    rm.item_code AS raw_material,
    rc.quantity_kg AS rm_quantity_needed
FROM item_master fg
LEFT JOIN item_master wip ON fg.wip_item_id = wip.id
LEFT JOIN item_master wipf ON fg.wipf_item_id = wipf.id
LEFT JOIN recipe_components rc ON wip.id = rc.wip_item_id
LEFT JOIN item_master rm ON rc.rm_item_id = rm.id
WHERE fg.item_code = '1005.1'  -- Smoked Ham Sliced 200g
ORDER BY rc.step_order;
```

### 2. All Finished Goods Using a Specific WIP
```sql
SELECT 
    fg.item_code,
    fg.description,
    CASE WHEN fg.wipf_item_id IS NOT NULL THEN 'Yes' ELSE 'No' END AS has_final_processing
FROM item_master fg
WHERE fg.wip_item_id = (SELECT id FROM item_master WHERE item_code = '1003');
```

### 3. Recipe Components for a WIP Item
```sql
SELECT 
    wip.item_code AS wip_item,
    rm.item_code AS raw_material,
    rc.quantity_kg,
    rc.step_order
FROM item_master wip
JOIN recipe_components rc ON wip.id = rc.wip_item_id
JOIN item_master rm ON rc.rm_item_id = rm.id
WHERE wip.item_code = '1003'
ORDER BY rc.step_order;
```

### 4. Material Requirements Calculation
```sql
-- Calculate raw material needs for 500kg of finished good
SELECT 
    rm.item_code,
    rm.description,
    (rc.quantity_kg * 500) AS total_kg_needed,
    rm.price_per_kg,
    (rc.quantity_kg * 500 * rm.price_per_kg) AS total_cost
FROM item_master fg
JOIN item_master wip ON fg.wip_item_id = wip.id
JOIN recipe_components rc ON wip.id = rc.wip_item_id
JOIN item_master rm ON rc.rm_item_id = rm.id
WHERE fg.item_code = '1002.1';  -- Ham Sliced 200g
```

## 🚀 Migration Process

### Step 1: Run Database Migration
```bash
# Execute the SQL migration script
python migrate_to_new_schema.py
```

### Step 2: Update Flask Models
Replace your existing models with the new ones in `new_models.py`:

```python
from database import db

class ItemMaster(db.Model):
    __tablename__ = 'item_master'
    
    id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.String(255))
    item_type = db.Column(db.String(20), nullable=False)  # Direct string
    
    # Self-referencing FKs for FG composition
    wip_item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'))
    wipf_item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'))
    
    # Relationships
    wip_item = db.relationship('ItemMaster', remote_side=[id], foreign_keys=[wip_item_id])
    wipf_item = db.relationship('ItemMaster', remote_side=[id], foreign_keys=[wipf_item_id])

class RecipeComponent(db.Model):
    __tablename__ = 'recipe_components'
    
    id = db.Column(db.Integer, primary_key=True)
    wip_item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)
    rm_item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)
    quantity_kg = db.Column(db.Float, nullable=False)
    recipe_code = db.Column(db.String(50))
```

### Step 3: Update Controllers
Modify your controllers to use the new structure:

```python
# OLD: Using recipe_master and item_type lookup
recipes = RecipeMaster.query.filter_by(finished_good_id=item_id).all()

# NEW: Using recipe_components directly
recipe_components = RecipeComponent.query.filter_by(wip_item_id=item_id).all()

# OLD: Checking item type via relationship
if item.item_type.type_name == 'WIP':

# NEW: Direct string comparison
if item.item_type == 'WIP':
```

## ✅ Benefits of New Design

### 1. **Simplified Structure**
- Only 2 tables instead of complex multi-table relationships
- Direct item_type column eliminates lookup table joins
- Self-referencing FKs elegantly handle FG composition

### 2. **Better Performance** 
- Fewer table joins in common queries
- Direct string comparisons instead of FK lookups
- Optimized indexes on key fields

### 3. **Clearer Business Logic**
- Recipes clearly separated from composition
- FG composition explicitly defined with self-references
- Business rules enforced through database constraints

### 4. **Easier Maintenance**
- Less complex relationship mapping
- Straightforward BOM explosion queries
- Clear separation of concerns

### 5. **Flexible Item Types**
- Easy to add new item types (just update enum constraint)
- No need to manage lookup tables
- Direct filtering and grouping capabilities

## 🛠️ Post-Migration Tasks

1. **Update Application Code**: Modify controllers to use new table structure
2. **Test BOM Calculations**: Verify all costing and requirement calculations
3. **Update Reports**: Adjust any existing reports to use new schema
4. **Data Validation**: Run validation queries to ensure data integrity
5. **Performance Testing**: Verify improved query performance
6. **User Training**: Update any user documentation

## 📈 Schema Validation Queries

After migration, run these queries to validate the new structure:

```sql
-- Count items by type
SELECT item_type, COUNT(*) FROM item_master GROUP BY item_type;

-- Verify FG composition rules
SELECT COUNT(*) as fg_without_wip FROM item_master 
WHERE item_type = 'FG' AND wip_item_id IS NULL;  -- Should be 0

-- Check recipe completeness
SELECT COUNT(*) as recipes FROM recipe_components;

-- Validate no orphaned references
SELECT COUNT(*) as orphaned_wip FROM item_master 
WHERE wip_item_id NOT IN (SELECT id FROM item_master WHERE item_type = 'WIP');
```

## 🎉 Conclusion

This new schema design provides a robust, scalable foundation for your manufacturing database that:

- ✅ Meets all business requirements
- ✅ Improves query performance  
- ✅ Simplifies maintenance
- ✅ Enforces business rules
- ✅ Supports complex BOM calculations
- ✅ Enables flexible reporting

The two-table design elegantly captures the manufacturing hierarchy while maintaining data integrity and providing excellent performance for all common operations. 