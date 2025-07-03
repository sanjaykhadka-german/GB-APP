# NEW DATABASE SCHEMA DESIGN - MANUFACTURING COMPANY

## Overview
This document outlines the redesigned manufacturing database schema using a simplified two-table design.

## New Schema Design

### Table 1: item_master (Unified Item Registry)
- All items (RM, WIP, WIPF, FG, Packaging) in one table
- Direct item_type column (no lookup table)
- Self-referencing FKs for FG composition

### Table 2: recipe_components (Bill of Materials)  
- Links WIP items to their RM components
- Stores quantity requirements
- Replaces complex recipe_master structure

## Sample Data
```sql
-- Raw Materials
INSERT INTO item_master (item_code, description, item_type, price_per_kg) VALUES
('RM-PORK', 'Pork Shoulder', 'RM', 8.50),
('RM-SPICE', 'Ham Seasoning', 'RM', 25.00);

-- WIP Item  
INSERT INTO item_master (item_code, description, item_type) VALUES
('1003', 'Ham Base - WIP', 'WIP');

-- Recipe Components
INSERT INTO recipe_components (wip_item_id, rm_item_id, quantity_kg) VALUES
((SELECT id FROM item_master WHERE item_code = '1003'),
 (SELECT id FROM item_master WHERE item_code = 'RM-PORK'), 100.000),
((SELECT id FROM item_master WHERE item_code = '1003'),
 (SELECT id FROM item_master WHERE item_code = 'RM-SPICE'), 25.000);

-- Finished Goods
INSERT INTO item_master (item_code, description, item_type, wip_item_id) VALUES
('1002.1', 'Ham Sliced 200g', 'FG', 
 (SELECT id FROM item_master WHERE item_code = '1003'));
```

## Migration Steps
1. Run `python migrate_to_new_schema.py`
2. Update Flask models with `new_models.py`
3. Test and validate data integrity
4. Update controllers to use new structure

## Benefits
- Simplified 2-table design
- Better performance (fewer joins)
- Clear business logic separation
- Easier maintenance and queries 