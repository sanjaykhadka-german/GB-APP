
# Controller Update Guide

## Key Changes Needed:

### 1. Replace joining table queries with ItemMaster queries
```python
# OLD:
joining = Joining.query.filter_by(fg_code=product_code).first()

# NEW:
item = ItemMaster.query.filter_by(item_code=product_code, item_type='Finished Good').first()
```

### 2. Update SOH queries
```python
# OLD:
soh = SOH.query.filter_by(fg_code=product_code, week_commencing=week).first()

# NEW:
item = ItemMaster.query.filter_by(item_code=product_code).first()
soh = SOH.query.filter_by(item_id=item.id, week_commencing=week).first()
```

### 3. Update Packing queries
```python
# OLD:
packing = Packing.query.filter_by(product_code=product_code).first()

# NEW:
item = ItemMaster.query.filter_by(item_code=product_code).first()
packing = Packing.query.filter_by(item_id=item.id).first()
```

### 4. Update Filling queries
```python
# OLD:
filling = Filling.query.filter_by(fill_code=fill_code).first()

# NEW:
wipf_item = ItemMaster.query.filter_by(item_code=fill_code, item_type='WIPF').first()
filling = Filling.query.filter_by(item_id=wipf_item.id).first()
```

### 5. Update Production queries
```python
# OLD:
production = Production.query.filter_by(production_code=prod_code).first()

# NEW:
wip_item = ItemMaster.query.filter_by(item_code=prod_code, item_type='WIP').first()
production = Production.query.filter_by(item_id=wip_item.id).first()
```

## Files to Update:
- controllers/soh_controller.py
- controllers/packing_controller.py
- controllers/filling_controller.py
- controllers/production_controller.py
- templates/item_master/create.html (add WIPF, WIP types)
- templates/item_master/edit.html (add WIPF, WIP types)
