#!/usr/bin/env python3
"""
Check inventory data
"""

from app import create_app
from database import db
from models.inventory import Inventory

def check_inventory_data():
    """Check inventory data"""
    app = create_app()
    
    with app.app_context():
        print("Checking inventory data...")
        
        # Get all inventory records
        inventory_records = Inventory.query.all()
        
        print(f"\nFound {len(inventory_records)} inventory records")
        
        for record in inventory_records:
            print(f"\nInventory Record:")
            print(f"Week Commencing: {record.week_commencing}")
            print(f"Item ID: {record.item_id}")
            print(f"Required Total: {record.required_total}")
            print(f"Category: {record.category}")
            print(f"Price per KG: {record.price_per_kg}")
            print(f"Value Required: {record.value_required}")
            print(f"Current Stock: {record.current_stock}")
            print(f"Supplier Name: {record.supplier_name}")
            print(f"Required for Plan: {record.required_for_plan}")
            print(f"Variance for Week: {record.variance_for_week}")
            print(f"Variance: {record.variance}")

if __name__ == '__main__':
    check_inventory_data() 