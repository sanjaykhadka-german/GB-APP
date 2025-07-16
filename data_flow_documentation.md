# Data Flow Documentation - Supply Chain Management System

## Overview
This document outlines the data flows in the supply chain management system for SOH (Stock on Hand), packing, filling, production, and inventory management.

## 1. Data Flow from SOH Upload → Packing → Filling → Production → Usage/Raw Material Reports → Inventory

### 1.1 SOH Upload Process
**Entry Point**: `soh_controller.py` - `/soh/upload` route

**Data Flow**:
1. **SOH Upload** → Excel file processed containing:
   - `fg_code` (item code)
   - `soh_total_units` (stock units)
   - `week_commencing` (week date)

2. **SOH Processing** → Creates/Updates SOH entries:
   ```python
   # models/soh.py
   class SOH:
       item_id = ForeignKey to ItemMaster
       week_commencing = Date
       soh_total_units = Float
       soh_total_boxes = Float
   ```

3. **Automatic Packing Creation** → For each SOH entry, creates packing record:
   ```python
   # In soh_controller.py - create_packing_entry_from_soh()
   requirement_kg = soh_requirement_kg_week  # What we need to pack
   requirement_unit = soh_requirement_units_week  # Units to pack
   ```

4. **Downstream Aggregation** → BOM Service creates filling and production entries:
   ```python
   # controllers/bom_service.py
   BOMService.update_downstream_requirements(week_commencing)
   ```

### 1.2 Packing → Filling → Production Flow
**Data Flow**:
1. **Packing Table** → Contains requirements for finished goods
2. **Filling Table** → Aggregated requirements for WIPF (Work in Progress - Filling) items
3. **Production Table** → Aggregated requirements for WIP (Work in Progress) items
4. **Usage Report Table** → Raw material usage based on recipes
5. **Raw Material Report Table** → Specific raw material requirements
6. **Inventory Table** → Daily stock tracking and planning

### 1.3 Recipe Explosion Process
**BOM Service Hierarchy**:
- **FG (Finished Goods)** → May have `wip_item_id` and `wipf_item_id`
- **WIPF (Work in Progress - Filling)** → Intermediate filling step
- **WIP (Work in Progress)** → Production step
- **Raw Materials** → Base ingredients

**Recipe Explosion**:
```python
# Example flow for item 2015.100.2
FG: 2015.100.2 (500 units needed)
  ↓ (via wipf_item_id)
WIPF: 2015.100 (aggregated from all FG variants)
  ↓ (via wip_item_id) 
WIP: 2015 (aggregated from all WIPF variants)
  ↓ (via recipes)
Raw Materials: Various ingredients with percentages
```

## 2. Data Flow When Creating a New SOH Entry Manually

### 2.1 Manual SOH Entry Process
**Entry Point**: `soh_controller.py` - `/soh/create` route

**Step-by-Step Flow**:
1. **User Input** → Manual form submission with:
   - Item code selection
   - Week commencing date
   - SOH units/boxes values

2. **SOH Record Creation**:
   ```python
   soh = SOH(
       item_id=item.id,
       week_commencing=week_commencing,
       soh_total_units=soh_units,
       soh_total_boxes=soh_boxes
   )
   ```

3. **Automatic Packing Creation** → Same as upload process:
   - Calculates `soh_requirement_units_week` based on item's `max_level - current_stock`
   - Creates packing entry with calculated requirements

4. **Downstream Effects**:
   - Triggers BOM service to update filling/production
   - Updates usage reports
   - Updates inventory calculations

## 3. Data Flow When Creating a New Packing Entry

### 3.1 Manual Packing Entry Process
**Entry Point**: `packing_controller.py` - `/packing/create` route

**Step-by-Step Flow**:
1. **User Input** → Form submission with:
   - Item code
   - Packing date
   - Special order KG (optional)
   - Requirement KG/units

2. **Packing Record Creation**:
   ```python
   packing = Packing(
       item_id=item.id,
       packing_date=packing_date,
       week_commencing=week_commencing,
       special_order_kg=special_order_kg,
       requirement_kg=requirement_kg,
       requirement_unit=requirement_unit
   )
   ```

3. **Automatic Downstream Creation**:
   - BOM service creates/updates filling entries for WIPF items
   - BOM service creates/updates production entries for WIP items
   - Usage reports generated based on recipes

4. **Calculation Logic**:
   ```python
   # In update_packing_entry function
   if soh_requirement_units_week and avg_weight_per_unit:
       requirement_kg = soh_requirement_units_week * avg_weight_per_unit
       
       # Add special order to requirements
       if special_order_kg and special_order_kg > 0:
           requirement_kg += special_order_kg
           special_order_units = special_order_kg / avg_weight_per_unit
           requirement_unit += special_order_units
   ```

## 4. Special Order KG Scenarios - Adding to Requirement KG

### 4.1 Scenario 1: Direct Special Order Addition
**Location**: `packing_controller.py` - `update_packing_entry()` function (lines 136-140)

**Logic**:
```python
# Calculate what we need to pack in KG
requirement_kg = soh_requirement_units_week * avg_weight_per_unit
requirement_unit = soh_requirement_units_week

# Add special order to requirements
if special_order_kg and special_order_kg > 0:
    requirement_kg += special_order_kg
    special_order_units = special_order_kg / avg_weight_per_unit
    requirement_unit += special_order_units
```

**Example**:
- SOH requirement: 100 units × 2.5 kg/unit = 250 kg
- Special order: 50 kg
- **Final requirement_kg: 250 + 50 = 300 kg**

### 4.2 Scenario 2: Bulk Edit Special Order
**Location**: `packing_controller.py` - `packing_bulk_edit()` function (lines 992)

**Logic**:
```python
packing.requirement_kg = round(total_stock_kg - soh_kg + packing.special_order_kg, 0)
```

**Example**:
- Total stock needed: 500 kg
- Current SOH: 200 kg
- Special order: 75 kg
- **Final requirement_kg: 500 - 200 + 75 = 375 kg**

### 4.3 Scenario 3: Inline Edit Special Order
**Location**: `packing_controller.py` - `packing_inline_edit()` function (lines 1087)

**Logic**:
```python
packing.requirement_kg = round(total_stock_kg - soh_kg + packing.special_order_kg, 0)
```

**Triggers**:
- When editing `special_order_kg` field in packing/list.html
- When editing `special_order_kg` field in packing/edit.html
- Automatic recalculation of requirement_kg

### 4.4 Scenario 4: Template-Based Updates
**Templates**: `packing/list.html` and `packing/edit.html`

**JavaScript Events**:
- Input field changes trigger AJAX calls to inline edit endpoint
- Form submissions trigger bulk edit operations
- Both update requirement_kg automatically

## 5. Testing Scenarios

### 5.1 Test Case 1: SOH Upload with Special Order
```python
# Test data
item_code = "2015.100.2"
week_commencing = "2024-01-01"
soh_units = 150
special_order_kg = 100

# Expected flow:
# 1. SOH created with 150 units
# 2. Packing created with calculated requirement + special order
# 3. Filling/Production updated via BOM service
# 4. Usage reports generated
```

### 5.2 Test Case 2: Manual Packing with Special Order
```python
# Test data
item_code = "2015.125.02"
packing_date = "2024-01-01"
special_order_kg = 75
avg_weight_per_unit = 2.5

# Expected calculation:
# requirement_kg = (normal_requirement * avg_weight) + special_order_kg
# requirement_unit = normal_requirement + (special_order_kg / avg_weight)
```

### 5.3 Test Case 3: Bulk Edit Special Order
```python
# Test scenario:
# 1. Navigate to packing/list.html
# 2. Use bulk edit modal to update special_order_kg
# 3. Verify requirement_kg is recalculated
# 4. Verify downstream entries are updated
```

### 5.4 Test Case 4: Inline Edit Special Order
```python
# Test scenario:
# 1. Navigate to packing/edit.html
# 2. Click on special_order_kg field
# 3. Change value and press Enter
# 4. Verify requirement_kg updates immediately
# 5. Verify downstream production/filling updates
```

## 6. Key Calculation Formulas

### 6.1 Packing Requirements
```python
# Base requirement from SOH
base_requirement_kg = soh_requirement_units_week * avg_weight_per_unit

# With special order
final_requirement_kg = base_requirement_kg + special_order_kg

# Unit calculation
special_order_units = special_order_kg / avg_weight_per_unit
final_requirement_unit = soh_requirement_units_week + special_order_units
```

### 6.2 Stock Calculations
```python
# SOH in KG
soh_kg = soh_total_units * avg_weight_per_unit

# Total stock after packing
total_stock_kg = soh_kg + requirement_kg
total_stock_units = soh_total_units + requirement_unit
```

### 6.3 Alternative Calculation (Used in bulk/inline edits)
```python
# Different approach used in some scenarios
requirement_kg = total_stock_kg - soh_kg + special_order_kg
requirement_unit = total_stock_units - soh_units + special_order_units
```

## 7. Data Dependencies

### 7.1 Required Master Data
- **ItemMaster**: item_code, description, avg_weight_per_unit, max_level, min_level
- **Machinery**: machinery assignments
- **Department**: department assignments
- **RecipeMaster**: recipe relationships and percentages

### 7.2 Calculation Dependencies
- **avg_weight_per_unit**: Required for KG ↔ Unit conversions
- **max_level/min_level**: Required for SOH requirement calculations
- **calculation_factor**: Used in stock calculations
- **recipe percentages**: Used in usage report generation

## 8. Error Handling

### 8.1 Common Scenarios
- Missing avg_weight_per_unit → Defaults to 0, may cause division errors
- Invalid dates → Validation and error messages
- Missing item relationships → Warnings in logs
- Database constraint violations → Rollback and error messages

### 8.2 Validation Rules
- special_order_kg must be >= 0
- requirement_kg cannot be negative
- Week commencing must be a Monday
- Item must exist in ItemMaster

## 9. Performance Considerations

### 9.1 Bulk Operations
- SOH upload processes multiple items in single transaction
- BOM service aggregates requirements efficiently
- Batch updates for downstream entries

### 9.2 Optimization Points
- Index on week_commencing for faster queries
- Batch processing for recipe explosions
- Caching of frequently accessed item data

## 10. Conclusion

The system follows a hierarchical data flow from SOH → Packing → Filling → Production → Reports → Inventory. Special order KG is consistently added to requirement_kg across all scenarios, ensuring accurate production planning and inventory management. The BOM service handles the complex recipe explosions and downstream updates automatically.