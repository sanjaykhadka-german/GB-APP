# Special Order KG Update Fix

## Problem Description

When editing the "special order KG" column in `packing/list.html`, the following columns become zero after page refresh:

**In production/list.html:**
- TOTAL PLANNED
- Variance to Required  
- monday_planned, tuesday_planned, wednesday_planned, thursday_planned, friday_planned, saturday_planned, sunday_planned

**In inventory/list.html:**
- Monday to Sunday columns (daily required kg values)

## Root Cause Analysis

The issue occurs in the re-aggregation process triggered when special order KG is updated:

1. **Packing Update**: Editing special order KG calls `update_cell` endpoint in `controllers/packing_controller.py`

2. **Re-aggregation Trigger**: This triggers `re_aggregate_filling_and_production_for_week()` which calls `BOMService.update_downstream_requirements()`

3. **Data Deletion**: In `controllers/bom_service.py`, the system **deletes ALL existing Production entries** for that week:
   ```python
   Production.query.filter_by(week_commencing=week_commencing).delete()
   ```

4. **New Entry Creation**: Creates **brand new Production entries** with only basic fields:
   ```python
   new_production = Production(
       production_date=week_commencing,
       week_commencing=week_commencing,
       item_id=wip_id,
       production_code=data['item'].item_code,
       total_kg=data['total_kg'],  # ✅ Updated correctly
       batches=data['total_kg'] / 300.0
       # ❌ NO planned fields set - they default to 0.0
   )
   ```

5. **Lost Data**: The new Production entries have **default values (0.0)** for all planned fields

6. **Inventory Impact**: Inventory daily values become zero because they depend on production planned values through recipe calculations

## Solution Implemented

### File: `controllers/bom_service.py`

**Before (Lines 151-177):**
```python
# Clear existing downstream entries for the week before creating new ones
Filling.query.filter_by(week_commencing=week_commencing).delete()
Production.query.filter_by(week_commencing=week_commencing).delete()  # ❌ This deletes planned values

# Create new Production entries
for wip_id, data in wip_aggregations.items():
    new_production = Production(...)  # ❌ Planned values default to 0.0
    db.session.add(new_production)
```

**After (Fixed):**
```python
# Clear existing downstream entries for the week before creating new ones
Filling.query.filter_by(week_commencing=week_commencing).delete()
# DON'T delete Production entries - we need to preserve planned values
# Production.query.filter_by(week_commencing=week_commencing).delete()

# Update or create Production entries (preserve planned values)
for wip_id, data in wip_aggregations.items():
    # Check for existing production entry
    existing_production = Production.query.filter_by(
        item_id=wip_id,
        week_commencing=week_commencing
    ).first()
    
    if existing_production:
        # Update existing entry - preserve all planned values ✅
        existing_production.total_kg = data['total_kg']
        existing_production.batches = data['total_kg'] / 300.0
        existing_production.production_code = data['item'].item_code
        existing_production.production_date = week_commencing
    else:
        # Create new entry only if none exists
        new_production = Production(...)
        db.session.add(new_production)

# Update inventory daily requirements based on preserved planned values ✅
try:
    from controllers.production_controller import update_inventory_daily_requirements
    update_inventory_daily_requirements(week_commencing)
except Exception as inv_error:
    logger.warning(f"Could not update inventory daily requirements: {inv_error}")
```

## What the Fix Does

1. **Preserves Production Planned Values**: Instead of deleting and recreating Production entries, the fix updates existing entries while preserving all planned values (total_planned, monday_planned, etc.)

2. **Updates Only Required Fields**: Only updates the fields that need to change (total_kg, batches, production_code, production_date)

3. **Maintains Inventory Daily Values**: Since production planned values are preserved, inventory daily calculations remain correct

4. **Ensures Data Consistency**: Adds inventory daily requirements update to ensure consistency after production updates

## Testing the Fix

The fix ensures that:

✅ **Special Order KG** updates correctly in packing  
✅ **Production total_kg** updates correctly  
✅ **Production planned values** are preserved (not reset to zero)  
✅ **Inventory daily values** remain correct (not reset to zero)  
✅ **Variance calculations** work correctly because planned values are maintained  

## Files Modified

1. **`controllers/bom_service.py`** - Modified `update_downstream_requirements()` method to preserve planned values
   - Removed Production entry deletion
   - Added update-or-create logic for Production entries
   - Added inventory daily requirements update

## Impact

This fix resolves the user's reported issue where editing special order KG in packing caused planned values and inventory daily values to become zero after page refresh.
