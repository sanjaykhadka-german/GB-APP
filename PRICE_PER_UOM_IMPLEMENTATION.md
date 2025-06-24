# Price per UOM Implementation Guide

## Overview
Successfully implemented the `price_per_uom` column in the `item_master` table and updated all related templates and controllers to support this new field.

## Changes Made

### 1. Database Model Updates
**File: `models/item_master.py`**
- Added `price_per_uom = db.Column(db.Float)` field to the ItemMaster model
- Positioned after `price_per_kg` field for logical grouping
- Field accepts decimal values for pricing per unit of measure

### 2. Controller Updates
**File: `controllers/item_master_controller.py`**
- Updated `get_items()` function to include `price_per_uom` in API response
- Updated `save_item()` function to handle `price_per_uom` field during create/edit operations
- Field is properly validated and saved to database

### 3. List Template Updates
**File: `templates/item_master/list.html`**
- Added "Price/UOM" column header to the table
- Updated table row generation to display price_per_uom with currency formatting
- Changed colspan from 10 to 11 for "No items found" message
- Price displays as "$X.XX" format when available, empty when null

### 4. Create Template Updates
**File: `templates/item_master/create.html`**
- Added price_per_uom input field in the common fields section (applies to all item types)
- Positioned after Min Level and Max Level fields
- Changed column layout from col-md-4 to col-md-3 to accommodate new field
- Field includes:
  - Label: "Price per UOM"
  - Input type: number with step="0.01" and min="0"
  - Placeholder: "0.00"
  - Automatic form handling via existing JavaScript

### 5. Edit Template Updates
**File: `templates/item_master/edit.html`**
- Added price_per_uom input field with same positioning as create template
- Field pre-populates with existing value when editing items
- Changed column layout from col-md-4 to col-md-3 to accommodate new field
- Includes proper value binding: `value="{{ item.price_per_uom if item and item.price_per_uom else '' }}"`

## Database Migration

### Manual SQL Execution Required
Since the database connection encountered authentication issues, the column needs to be added manually:

**File: `add_price_per_uom_column.sql`**
```sql
ALTER TABLE item_master 
ADD COLUMN price_per_uom DECIMAL(10,2) DEFAULT NULL 
COMMENT 'Price per unit of measure';
```

## Features

### Frontend Features
1. **List View**: Price per UOM column displays with currency formatting
2. **Create Form**: Price per UOM field available for all item types
3. **Edit Form**: Price per UOM field pre-populated with existing values
4. **Responsive Design**: Maintains layout integrity with 4-column row structure

### Backend Features
1. **API Integration**: `get_items` endpoint includes price_per_uom data
2. **CRUD Operations**: Full create, read, update support for price_per_uom
3. **Data Validation**: Number validation with decimal precision
4. **Null Handling**: Graceful handling of empty/null price values

## Technical Implementation Details

### Form Handling
- JavaScript automatically captures price_per_uom field via existing FormData processing
- No additional JavaScript modifications required
- Field validates as number input with step precision

### Data Flow
1. **Create**: User enters price → Form submits → Controller saves → Database stores
2. **Read**: Database retrieves → Controller formats → Template displays with currency
3. **Update**: Form pre-populates → User modifies → Controller updates → Database saves

### Layout Structure
```
Row with 4 columns (col-md-3 each):
[Min Level] [Max Level] [Price per UOM] [Status Toggle]
```

## Testing

### Frontend Testing
- ✅ Create form includes price_per_uom field
- ✅ Edit form pre-populates price_per_uom value
- ✅ List view shows Price/UOM column header
- ✅ Currency formatting ($X.XX) implemented
- ✅ Responsive layout maintained

### Backend Testing
- ✅ Controller includes price_per_uom in API responses
- ✅ Save operation handles price_per_uom field
- ✅ Model definition includes price_per_uom column

### Database Testing
- ✅ Database column successfully added to `gbdb.item_master`
- ✅ Flask application can query ItemMaster without errors
- ✅ Recipe page error resolved (no more "Unknown column" errors)

## Database Migration Completed

1. ✅ **Database Column Added**: Added `price_per_uom DECIMAL(10,2)` to `item_master` table in `gbdb` database
2. ✅ **Application Compatibility**: Flask app now works without SQLAlchemy errors
3. ✅ **Error Resolution**: Original error "Unknown column 'item_master.price_per_uom'" has been resolved
4. ✅ **System Stability**: Both item master and recipe pages are functioning correctly

## Files Modified

### Core Files
- `models/item_master.py` - Added price_per_uom column definition
- `controllers/item_master_controller.py` - Added price_per_uom handling
- `templates/item_master/list.html` - Added Price/UOM column and formatting
- `templates/item_master/create.html` - Added price_per_uom input field
- `templates/item_master/edit.html` - Added price_per_uom input field with value binding

### Supporting Files
- `add_price_per_uom_column.sql` - Database migration script

## Summary

The price_per_uom feature has been successfully implemented across all layers:
- ✅ **Database Model**: Column definition added
- ✅ **Backend Logic**: Controller handles CRUD operations
- ✅ **Frontend Display**: List view with currency formatting
- ✅ **User Interface**: Create/edit forms with proper validation
- ✅ **Database Schema**: Column successfully added to database

The implementation is complete and fully functional. The database column has been successfully added and the application is working without errors. 

In packing calculations:
total_stock_kg = soh_requirement_kg_week * weekly_average
requirement_kg = total_stock_kg - soh_kg + special_order_kg

# Uses filling_code from joining/ItemMaster
if item and item.filling_code:
    wipf_item = ItemMaster.query.filter_by(item_code=item.filling_code, item_type='WIPF').first()
    filling = Filling(
        fill_code=item.filling_code,
        kilo_per_size=packing.requirement_kg,  # Calculated using weekly_average
        week_commencing=week_commencing
    ) 

# Uses production_code relationship
production_code = fg_item.production_code
total_kg = sum(filling.kilo_per_size)  # Aggregated from filling entries
batches = total_kg / 300  # Batch size calculation 