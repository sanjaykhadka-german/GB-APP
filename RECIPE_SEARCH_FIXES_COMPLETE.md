# Recipe Search and Percentage Column Fixes - Complete

## Issues Resolved

### 1. Missing Percentage Column
**Problem**: The `percentage` column was missing from the recipe_master table after the migration.

**Solution**:
- Added `percentage` column back to the database
- Updated `RecipeMaster` model to include the percentage field
- Implemented automatic percentage calculation for all recipe operations

### 2. SQLAlchemy Query Error in Search
**Problem**: The search functionality was failing with "Select statement returned no FROM clauses due to auto-correlation" error.

**Solution**:
- Fixed the complex nested subquery in `get_search_recipes` endpoint
- Used proper SQLAlchemy aliases for multiple joins to ItemMaster table
- Replaced problematic `add_columns` with nested subqueries with proper join syntax

### 3. Frontend-Backend Field Name Mismatch
**Problem**: The frontend template was using old field names while the backend expected new field names:
- Frontend: `raw_material_code`, `raw_material`, `kg_per_batch`
- Backend: `component_code`, `component_name`, `quantity_required`

**Solution**: Updated the frontend template to use correct field names

## Changes Made

### 1. Database Changes
```sql
-- Added percentage column back
ALTER TABLE recipe_master ADD COLUMN percentage FLOAT;
```

### 2. Model Updates (`models/recipe_master.py`)
```python
# Added percentage column to the model
percentage = db.Column(db.Float)
```

### 3. Controller Updates (`controllers/recipe_controller.py`)

#### Fixed Search Query
```python
# Before: Problematic nested subqueries
recipes_query = recipes_query.add_columns(
    db.session.query(ItemMaster.item_code).filter(ItemMaster.id == RecipeMaster.assembly_item_id).label('assembly_code'),
    db.session.query(ItemMaster.description).filter(ItemMaster.id == RecipeMaster.assembly_item_id).label('assembly_name')
)

# After: Proper aliases and joins
from sqlalchemy.orm import aliased
ComponentItem = aliased(ItemMaster)
AssemblyItem = aliased(ItemMaster)

recipes_query = db.session.query(
    RecipeMaster,
    ComponentItem.item_code.label('component_code'),
    ComponentItem.description.label('component_name'),
    AssemblyItem.item_code.label('assembly_code'),
    AssemblyItem.description.label('assembly_name')
).join(
    ComponentItem,
    RecipeMaster.component_item_id == ComponentItem.id
).join(
    AssemblyItem,
    RecipeMaster.assembly_item_id == AssemblyItem.id
)
```

#### Added Percentage Calculation
```python
# After recipe creation/editing
recipe_code = recipes_data[0]['recipe_code']
recipes_to_update = RecipeMaster.query.filter(
    RecipeMaster.recipe_code == recipe_code
).all()

total_quantity = sum(float(r.quantity_required) for r in recipes_to_update)
for r in recipes_to_update:
    r.percentage = Decimal(round((float(r.quantity_required) / total_quantity) * 100, 2)) if total_quantity > 0 else Decimal('0.00')
```

#### Updated Response Data
```python
# Added percentage to search response
"percentage": float(recipe.RecipeMaster.percentage) if recipe.RecipeMaster.percentage else 0.00,
```

### 4. Frontend Template Updates (`templates/recipe/recipe.html`)

#### Updated Table Headers
```html
<!-- Before -->
<th>Raw Material Code</th>
<th>Raw Material</th>
<th>Kg per Batch</th>

<!-- After -->
<th>Component Code</th>
<th>Component Material</th>
<th>Quantity Required</th>
```

#### Updated Search Results Display
```javascript
// Before
row.innerHTML = `
    <td>${recipe.raw_material_code}</td>
    <td>${recipe.raw_material}</td>
    <td>${parseFloat(recipe.kg_per_batch).toFixed(3)}</td>
    <td>${parseFloat(recipe.percentage).toFixed(2)}%</td>
`;

// After
row.innerHTML = `
    <td>${recipe.component_code}</td>
    <td>${recipe.component_name}</td>
    <td>${parseFloat(recipe.quantity_required).toFixed(3)}</td>
    <td>${parseFloat(recipe.percentage).toFixed(2)}%</td>
`;
```

#### Updated Form Field Names
```html
<!-- Before -->
<select name="raw_material_id" required>
<select name="finished_good_id" required>
<input type="number" name="kg_per_batch">

<!-- After -->
<select name="component_item_id" required>
<select name="assembly_item_id" required>
<input type="number" name="quantity_required">
```

#### Updated Form Submission
```javascript
// Before
recipes.push({
    raw_material_id: selects[0].value,
    finished_good_id: selects[1].value,
    kg_per_batch: inputs[2].value
});

// After
recipes.push({
    component_item_id: selects[0].value,
    assembly_item_id: selects[1].value,
    quantity_required: inputs[2].value
});
```

## Percentage Calculation Logic

### Automatic Calculation
Percentages are automatically calculated whenever:
1. A new recipe is created
2. An existing recipe is updated
3. A recipe is deleted

### Formula
```
percentage = (quantity_required / total_quantity_for_recipe_code) * 100
```

### Scope
Percentages are calculated per `recipe_code`, meaning all components for the same recipe code sum to 100%.

## Data Migration

### Existing Data Update
All existing recipes (383 records) were updated with calculated percentages:
```python
# Example percentages calculated
Recipe Code 2006: 15 recipes, total quantity: 106.95
Recipe Code 6002: 15 recipes, total quantity: 108.44
Recipe Code 2005: 14 recipes, total quantity: 109.43
# ... and so on
```

## Testing Results

### Search Functionality
- ✅ Search by recipe code works correctly
- ✅ Search by description works correctly
- ✅ Proper field names returned: `component_code`, `component_name`, `quantity_required`, `percentage`
- ✅ No more SQLAlchemy errors

### Percentage Display
- ✅ Percentages display correctly in search results
- ✅ Percentages are automatically calculated and updated
- ✅ Example: Recipe 2006 shows components with percentages: 37.40%, 18.70%, 23.38%, 14.03%

### Form Operations
- ✅ Add recipe form uses correct field names
- ✅ Edit recipe form uses correct field names
- ✅ Form submission sends correct data structure
- ✅ Backend processes new field names correctly

## Files Modified

1. `models/recipe_master.py` - Added percentage column
2. `controllers/recipe_controller.py` - Fixed query, added percentage calculation
3. `templates/recipe/recipe.html` - Updated all field names and display logic

## Final Status

✅ **All Issues Resolved**
- Percentage column added and working
- Search functionality restored
- Frontend-backend field mapping corrected
- Automatic percentage calculation implemented
- Application starts and runs without errors

The recipe search now correctly displays:
- Component Code (from item_master.item_code)
- Component Material (from item_master.description)  
- Quantity Required (recipe_master.quantity_required)
- Percentage (automatically calculated)

All 383 existing recipes have been updated with proper percentages and the system supports the new flexible multi-level manufacturing schema. 