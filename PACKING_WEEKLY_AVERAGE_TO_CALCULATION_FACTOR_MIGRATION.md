# Packing Weekly Average to Calculation Factor Migration

## Overview
This document outlines the complete migration from `weekly_average` to `calculation_factor` in the packing module. The change affects the database schema, model definitions, controllers, and templates.

## Changes Made

### 1. Database Schema Changes

#### Table: `packing`
**Column Rename:** `weekly_average` → `calculation_factor`

```sql
-- SQL to execute on database
ALTER TABLE packing 
CHANGE COLUMN weekly_average calculation_factor FLOAT DEFAULT 0.0;
```

### 2. Model Changes

#### File: `models/packing.py`
```python
# OLD
weekly_average = db.Column(db.Float, default=0.0, nullable=True)

# NEW  
calculation_factor = db.Column(db.Float, default=0.0, nullable=True)
```

### 3. Controller Changes

#### File: `controllers/packing_controller.py`
- Updated all references from `weekly_average` to `calculation_factor`
- Updated function parameters in `update_packing_entry()`
- Updated form field processing in create/edit routes
- Updated bulk edit functionality
- Updated cell update functionality
- Updated export functionality

#### File: `controllers/soh_controller.py`  
- Updated all calls to `update_packing_entry()` to use `calculation_factor` parameter
- Updated comments referencing the field

### 4. Template Changes

#### File: `templates/packing/list.html`
- Updated column header: "Weekly Average" → "Calculation Factor"
- Updated column visibility toggle label
- Updated bulk edit modal form field
- Updated JavaScript references
- Updated data table rendering

#### File: `templates/packing/create.html`
- Updated form field label and input name/id
- Updated from `weekly_average` to `calculation_factor`

#### File: `templates/packing/edit.html`
- Updated table header
- Updated editable cell data field references
- Updated bulk edit modal form
- Updated JavaScript condition in `updateCell` function

### 5. Migration Scripts Created

#### Files Created:
1. `rename_packing_column.py` - Python script for database migration
2. `rename_packing_column.sql` - Direct SQL script
3. `migrations/versions/rename_weekly_average_to_calculation_factor.py` - Alembic migration

## Migration Steps

### Step 1: Backup Database
```bash
# Create backup before making changes
mysqldump -u username -p database_name > backup_before_calculation_factor_migration.sql
```

### Step 2: Run Database Migration

**Option A: Using SQL Script (Recommended)**
```bash
mysql -u username -p database_name < rename_packing_column.sql
```

**Option B: Using Python Script**
```bash
# Update database credentials in script first
python rename_packing_column.py
```

**Option C: Manual SQL**
```sql
ALTER TABLE packing 
CHANGE COLUMN weekly_average calculation_factor FLOAT DEFAULT 0.0;
```

### Step 3: Verify Migration
```sql
-- Check table structure
DESCRIBE packing;

-- Verify column exists
SELECT COUNT(*) as total_records FROM packing;
SELECT COUNT(*) as records_with_calculation_factor 
FROM packing WHERE calculation_factor IS NOT NULL;
```

### Step 4: Update Application Code
All application code changes have been completed in this migration:

- ✅ Model definition updated
- ✅ Controller logic updated  
- ✅ Templates updated
- ✅ JavaScript updated
- ✅ Form processing updated

### Step 5: Test Application
1. Start the application
2. Navigate to packing module
3. Test create, edit, list, and bulk edit functionality
4. Verify calculations work correctly
5. Test column visibility toggles
6. Test search and sort functionality

## Files Modified

### Core Application Files
- `models/packing.py`
- `controllers/packing_controller.py`
- `controllers/soh_controller.py`
- `templates/packing/list.html`
- `templates/packing/create.html`
- `templates/packing/edit.html`

### Migration Files Created
- `rename_packing_column.py`
- `rename_packing_column.sql`
- `migrations/versions/rename_weekly_average_to_calculation_factor.py`

## Rollback Instructions

If rollback is needed:

### Database Rollback
```sql
ALTER TABLE packing 
CHANGE COLUMN calculation_factor weekly_average FLOAT DEFAULT 0.0;
```

### Code Rollback
Reverse all the changes listed above, changing `calculation_factor` back to `weekly_average`.

## Verification Checklist

- [ ] Database column renamed successfully
- [ ] Application starts without errors
- [ ] Packing list page loads correctly
- [ ] Create packing form works
- [ ] Edit packing functionality works
- [ ] Bulk edit functionality works
- [ ] Column visibility toggles work
- [ ] Search and sort functionality works
- [ ] Calculations are accurate
- [ ] SOH integration still works

## Notes

1. **Field Purpose**: The field represents a calculation factor used in stock and production planning calculations, specifically in the formula: `total_stock_kg = soh_requirement_kg_week * calculation_factor`

2. **Data Preservation**: The migration preserves all existing data values - only the column name changes.

3. **Compatibility**: All existing functionality remains the same, only the naming is more descriptive.

4. **Related Fields**: This change does not affect other fields in the packing table or related tables.

## Support

If issues arise during migration:
1. Check database connection settings
2. Verify column exists in database
3. Check application logs for errors
4. Ensure all files were properly updated
5. Test with a single record first

## Migration Date
**Completed:** [Insert completion date here]
**Tested:** [Insert test date here] 