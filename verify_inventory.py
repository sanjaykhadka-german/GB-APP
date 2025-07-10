from app import app
from models.inventory import Inventory

with app.app_context():
    count = Inventory.query.count()
    print(f"Total inventory records: {count}")
    
    if count > 0:
        record = Inventory.query.first()
        print(f"\nFirst record:")
        print(f"Item: {record.item.item_code} - {record.item.description}")
        print(f"Required Total: {record.required_total}")
        print(f"Current Stock: {record.current_stock}")
        print(f"Value Required: {record.value_required}")
        print(f"Required for Plan: {record.required_for_plan}")
        print(f"Variance: {record.variance}") 