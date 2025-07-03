# Exact Schema Transformation Guide

## Overview
This guide explains how to transform your current complex `item_master` and `recipe_master` tables to match your exact simplified specifications.

## Current Schema Issues
Your current models have grown complex over time with many extra columns that are not needed for your core business logic. You want to simplify to exactly the schema you specified.

## Target Schema

### ItemMaster Table (Simplified)
```python
class ItemMaster(db.Model):
    """
    Central table for all items in the system.
    Contains self-referencing relationships for FG composition.
    """
    __tablename__ = 'item_master'

    # Core identification
    id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255), nullable=False)
    
    # Item type (using lookup table)
    item_type_id = db.Column(db.Integer, db.ForeignKey('item_type.id'), nullable=False)
    
    # Simple string fields (converted from foreign keys)
    category = db.Column(db.String(100))
    department = db.Column(db.String(100))
    machinery = db.Column(db.String(100))
    
    # Stock and pricing
    min_stock = db.Column(db.DECIMAL(10, 2), default=0.00)
    max_stock = db.Column(db.DECIMAL(10, 2), default=0.00)
    price_per_kg = db.Column(db.DECIMAL(12, 4), nullable=True)
    
    # Operational fields
    is_active = db.Column(db.Boolean, default=True)
    is_make_to_order = db.Column(db.Boolean, default=False)
    loss_percentage = db.Column(db.DECIMAL(5, 2), default=0.00)
    calculation_factor = db.Column(db.DECIMAL(10, 4), default=1.0000)

    # FG Composition (Self-referencing Foreign Keys)
    wip_item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=True)
    wipf_item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=True)
```

### RecipeMaster Table (Simplified)
```python
class RecipeMaster(db.Model):
    """
    Association table defining the Bill of Materials for a WIP item.
    Links a WIP item (recipe_wip) to its Raw Material components (component_rm).
    """
    __tablename__ = 'recipe_master'

    id = db.Column(db.Integer, primary_key=True)
    quantity_kg = db.Column(db.DECIMAL(10, 4), nullable=False)

    # Foreign key to the WIP item being defined
    recipe_wip_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)
    
    # Foreign key to the RM component being used
    component_rm_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)
```

## Transformation Steps

### Step 1: Backup Current Tables
```sql
CREATE TABLE item_master_backup_pre_simplification AS SELECT * FROM item_master;
CREATE TABLE recipe_master_backup_pre_simplification AS SELECT * FROM recipe_master;
```

### Step 2: Transform item_master

#### 2a. Convert Foreign Keys to Strings
```sql
-- Convert category_id to category string
UPDATE item_master im
LEFT JOIN category c ON im.category_id = c.id
SET im.category = c.category_name
WHERE im.category_id IS NOT NULL;

-- Convert department_id to department string  
UPDATE item_master im
LEFT JOIN department d ON im.department_id = d.department_id
SET im.department = d.department_name
WHERE im.department_id IS NOT NULL;

-- Convert machinery_id to machinery string
UPDATE item_master im
LEFT JOIN machinery m ON im.machinery_id = m.machineID
SET im.machinery = m.machine_name
WHERE im.machinery_id IS NOT NULL;
```

#### 2b. Update Column Types
```sql
ALTER TABLE item_master 
MODIFY COLUMN item_code VARCHAR(50) NOT NULL,
MODIFY COLUMN description VARCHAR(255) NOT NULL,
MODIFY COLUMN category VARCHAR(100),
MODIFY COLUMN department VARCHAR(100), 
MODIFY COLUMN machinery VARCHAR(100),
MODIFY COLUMN min_stock DECIMAL(10,2) DEFAULT 0.00,
MODIFY COLUMN max_stock DECIMAL(10,2) DEFAULT 0.00,
MODIFY COLUMN price_per_kg DECIMAL(12,4),
MODIFY COLUMN loss_percentage DECIMAL(5,2) DEFAULT 0.00,
MODIFY COLUMN calculation_factor DECIMAL(10,4) DEFAULT 1.0000;
```

#### 2c. Add Self-Referencing Foreign Keys
```sql
ALTER TABLE item_master 
ADD COLUMN wip_item_id INT NULL,
ADD COLUMN wipf_item_id INT NULL,
ADD FOREIGN KEY (wip_item_id) REFERENCES item_master(id),
ADD FOREIGN KEY (wipf_item_id) REFERENCES item_master(id);
```

#### 2d. Remove Extra Columns
```sql
ALTER TABLE item_master 
DROP COLUMN category_id,
DROP COLUMN department_id,
DROP COLUMN machinery_id,
DROP COLUMN uom_id,
DROP COLUMN min_level,
DROP COLUMN max_level,
DROP COLUMN price_per_uom,
DROP COLUMN kg_per_unit,
DROP COLUMN units_per_bag,
DROP COLUMN avg_weight_per_unit,
DROP COLUMN supplier_name,
DROP COLUMN fw,
DROP COLUMN created_by_id,
DROP COLUMN updated_by_id,
DROP COLUMN created_at,
DROP COLUMN updated_at,
DROP COLUMN item_type;  -- Remove direct string, keep lookup
```

### Step 3: Transform recipe_master

#### 3a. Create New Table Structure
```sql
CREATE TABLE recipe_master_new (
    id INT PRIMARY KEY AUTO_INCREMENT,
    quantity_kg DECIMAL(10,4) NOT NULL,
    recipe_wip_id INT NOT NULL,
    component_rm_id INT NOT NULL,
    FOREIGN KEY (recipe_wip_id) REFERENCES item_master(id),
    FOREIGN KEY (component_rm_id) REFERENCES item_master(id),
    UNIQUE KEY uq_recipe_component (recipe_wip_id, component_rm_id)
);
```

#### 3b. Migrate Data
```sql
INSERT INTO recipe_master_new (quantity_kg, recipe_wip_id, component_rm_id)
SELECT 
    COALESCE(kg_per_batch, 0) as quantity_kg,
    finished_good_id as recipe_wip_id,
    raw_material_id as component_rm_id
FROM recipe_master
WHERE finished_good_id IS NOT NULL 
AND raw_material_id IS NOT NULL;
```

#### 3c. Replace Old Table
```sql
DROP TABLE recipe_master;
RENAME TABLE recipe_master_new TO recipe_master;
```

## Migration Script Usage

### Automated Migration
Run the migration script to perform all transformations automatically:

```bash
python migrate_to_exact_schema.py
```

### Manual Migration  
If you prefer to run SQL commands manually, execute the SQL statements from the sections above in order.

## Data Mapping

### item_master Mapping
| Current Column | New Column | Transformation |
|----------------|------------|----------------|
| id | id | No change |
| item_code | item_code | Type change to VARCHAR(50) |
| description | description | Type change to VARCHAR(255) NOT NULL |
| item_type_id | item_type_id | Keep as-is |
| category_id | category | Convert FK to string via JOIN |
| department_id | department | Convert FK to string via JOIN |
| machinery_id | machinery | Convert FK to string via JOIN |
| min_level | min_stock | Rename + type change |
| max_level | max_stock | Rename + type change |
| price_per_kg | price_per_kg | Type change to DECIMAL(12,4) |
| loss_percentage | loss_percentage | Type change to DECIMAL(5,2) |
| calculation_factor | calculation_factor | Type change to DECIMAL(10,4) |
| (new) | wip_item_id | Add self-referencing FK |
| (new) | wipf_item_id | Add self-referencing FK |
| All other columns | (removed) | Drop extra columns |

### recipe_master Mapping  
| Current Column | New Column | Transformation |
|----------------|------------|----------------|
| id | id | No change |
| kg_per_batch | quantity_kg | Rename + type change to DECIMAL(10,4) |
| finished_good_id | recipe_wip_id | Rename (semantic change) |
| raw_material_id | component_rm_id | Rename (semantic change) |
| All other columns | (removed) | Drop extra columns |

## Benefits of Simplified Schema

1. **Cleaner Data Model**: Only essential columns remain
2. **Better Performance**: Fewer columns to process
3. **Easier Maintenance**: Less complex relationships
4. **Clear Semantics**: Column names match business logic
5. **Self-Referencing FKs**: Elegant FG composition
6. **Simplified Queries**: Direct string comparisons instead of JOINs

## Verification Queries

After migration, verify the schema:

```sql
-- Check item_master structure
DESCRIBE item_master;

-- Check recipe_master structure  
DESCRIBE recipe_master;

-- Verify data counts
SELECT COUNT(*) FROM item_master;
SELECT COUNT(*) FROM recipe_master;

-- Test FG composition
SELECT 
    fg.item_code as fg_code,
    wip.item_code as wip_code,
    wipf.item_code as wipf_code
FROM item_master fg
LEFT JOIN item_master wip ON fg.wip_item_id = wip.id
LEFT JOIN item_master wipf ON fg.wipf_item_id = wipf.id
WHERE fg.wip_item_id IS NOT NULL OR fg.wipf_item_id IS NOT NULL;

-- Test recipe relationships
SELECT 
    wip.item_code as wip_code,
    rm.item_code as rm_code,
    r.quantity_kg
FROM recipe_master r
JOIN item_master wip ON r.recipe_wip_id = wip.id
JOIN item_master rm ON r.component_rm_id = rm.id
LIMIT 10;
```

## Rollback Plan

If you need to rollback:

```sql
-- Restore item_master
DROP TABLE item_master;
RENAME TABLE item_master_backup_pre_simplification TO item_master;

-- Restore recipe_master
DROP TABLE recipe_master;
RENAME TABLE recipe_master_backup_pre_simplification TO recipe_master;
```

## Next Steps

1. **Run Migration**: Execute `migrate_to_exact_schema.py`
2. **Update Controllers**: Modify controllers to use new schema
3. **Update Templates**: Update forms and displays
4. **Test Functionality**: Verify all features work with simplified schema
5. **Remove Backup Tables**: After confirming everything works

Your database will then exactly match your specified schema requirements with clean, simple relationships that support your business logic. 