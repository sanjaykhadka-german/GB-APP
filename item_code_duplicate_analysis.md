# Item Code Duplicate Analysis: WIP Products

## Problem Statement

You have two WIP products that need to be added to the item master:
- **1007 - HF Pulled pork - WIP**
- **1007 - GB Pulled Pork - WIP**

Both share the same `item_code` (1007) but have different descriptions (HF vs GB variants). These need separate recipes since they are different WIP products.

## Current System Constraints

Based on your current `item_master` model:
```python
item_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
```

**The current system enforces a UNIQUE constraint on `item_code`**, which prevents adding both items with the same code.

## Available Options

### Option 1: Modify Item Codes (Quick Fix)
**Implementation**: Add suffixes to differentiate the item codes
- `1007-HF` - HF Pulled pork - WIP
- `1007-GB` - GB Pulled Pork - WIP

**Pros**:
- Minimal code changes
- Maintains current database structure
- Easy to implement immediately

**Cons**:
- Changes established item coding conventions
- May affect existing integrations
- Requires updating all references to item code 1007

### Option 2: Composite Key (item_code + description)
**Implementation**: Remove unique constraint on `item_code` alone and create composite unique constraint

**Database Changes Required**:
```sql
-- Remove existing unique constraint
ALTER TABLE item_master DROP INDEX item_code;

-- Add composite unique constraint
ALTER TABLE item_master ADD CONSTRAINT uq_item_code_description 
    UNIQUE (item_code, description);
```

**Model Changes Required**:
```python
class ItemMaster(db.Model):
    # Remove unique=True from item_code
    item_code = db.Column(db.String(50), nullable=False, index=True)
    description = db.Column(db.String(255), nullable=False)
    
    # Add composite unique constraint
    __table_args__ = (
        db.UniqueConstraint('item_code', 'description', name='uq_item_code_description'),
    )
```

### Option 3: Variant/Sub-Product System
**Implementation**: Add a variant field to distinguish between sub-products

**Model Changes**:
```python
class ItemMaster(db.Model):
    item_code = db.Column(db.String(50), nullable=False, index=True)
    variant = db.Column(db.String(10), nullable=True)  # 'HF', 'GB', etc.
    description = db.Column(db.String(255), nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('item_code', 'variant', name='uq_item_code_variant'),
    )
```

### Option 4: Hierarchical Item Coding
**Implementation**: Create parent-child relationships for product variants

**Structure**:
- Parent: `1007` (Pulled Pork Base)
- Children: `1007.1` (HF variant), `1007.2` (GB variant)

## Recommended Solution: Option 2 (Composite Key)

### Why This Is the Best Option:

1. **Preserves Business Logic**: Maintains the same item code for related products
2. **Scalable**: Handles future cases of same item code with different variants
3. **Data Integrity**: Still prevents true duplicates (same code + same description)
4. **Minimal Disruption**: Doesn't change existing item codes

### Implementation Steps for Composite Key Solution:

#### 1. Update Database Schema
```sql
-- Backup current data
CREATE TABLE item_master_backup AS SELECT * FROM item_master;

-- Remove unique constraint on item_code
ALTER TABLE item_master DROP INDEX item_code;

-- Add composite unique constraint
ALTER TABLE item_master ADD CONSTRAINT uq_item_code_description 
    UNIQUE (item_code, description);

-- Recreate index for performance
CREATE INDEX idx_item_code ON item_master (item_code);
```

#### 2. Update Application Code

**Model Update** (`models/item_master.py`):
```python
class ItemMaster(db.Model):
    item_code = db.Column(db.String(50), nullable=False, index=True)  # Remove unique=True
    description = db.Column(db.String(255), nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('item_code', 'description', name='uq_item_code_description'),
    )
```

**Query Updates**: All queries that search by item_code alone need review:
```python
# OLD - This may return multiple results now
item = ItemMaster.query.filter_by(item_code='1007').first()

# NEW - Need to be more specific
item = ItemMaster.query.filter_by(item_code='1007', description='HF Pulled pork - WIP').first()

# OR get all variants
items = ItemMaster.query.filter_by(item_code='1007').all()
```

#### 3. Update UI Components

**Search Functions**: Update autocomplete and search to show both code and description
**Forms**: Ensure item selection includes both fields
**Reports**: Display full item identification (code + description)

#### 4. Migration Script

```python
def migrate_to_composite_key():
    """
    Migration script to implement composite key solution
    """
    # 1. Check for existing duplicates
    duplicates = db.session.execute(text("""
        SELECT item_code, COUNT(*) as count 
        FROM item_master 
        GROUP BY item_code 
        HAVING COUNT(*) > 1
    """)).fetchall()
    
    if duplicates:
        print("WARNING: Existing duplicates found:")
        for dup in duplicates:
            print(f"  {dup.item_code}: {dup.count} occurrences")
    
    # 2. Remove unique constraint
    db.session.execute(text("ALTER TABLE item_master DROP INDEX item_code"))
    
    # 3. Add composite constraint
    db.session.execute(text("""
        ALTER TABLE item_master 
        ADD CONSTRAINT uq_item_code_description 
        UNIQUE (item_code, description)
    """))
    
    # 4. Recreate index
    db.session.execute(text("CREATE INDEX idx_item_code ON item_master (item_code)"))
    
    db.session.commit()
```

## Problems with Current Project (If Using Composite Key)

### 1. **Query Updates Required**
- All existing queries using `filter_by(item_code=...)` need review
- Some may return multiple results unexpectedly
- Risk of application errors if not properly updated

### 2. **UI/UX Impact**
- Item selection dropdowns need updating
- Search results need to show full identification
- User training may be required

### 3. **Integration Points**
- External systems expecting unique item codes
- Import/export processes
- Reporting systems

### 4. **Data Validation**
- Need stronger validation to prevent accidental duplicates
- Business rules for when same item_code is acceptable

## Testing Strategy

### 1. **Database Integrity Tests**
```python
def test_composite_key_constraint():
    # Should allow same code, different description
    item1 = ItemMaster(item_code='1007', description='HF Pulled pork - WIP')
    item2 = ItemMaster(item_code='1007', description='GB Pulled Pork - WIP')
    
    # Should prevent exact duplicates
    item3 = ItemMaster(item_code='1007', description='HF Pulled pork - WIP')
    # This should raise IntegrityError
```

### 2. **Application Tests**
- Test all search functions
- Verify recipe associations work correctly
- Check reporting accuracy

### 3. **Performance Tests**
- Ensure query performance is acceptable
- Monitor index usage

## Conclusion

The **Composite Key approach (Option 2)** is recommended because it:
- Solves the immediate problem elegantly
- Maintains business logic integrity
- Provides scalability for future similar cases
- Requires manageable code changes

However, it requires careful planning and testing to ensure all application components are properly updated to handle the new constraint structure.