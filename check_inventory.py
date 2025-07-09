from app import app
from database import db
from models.inventory import Inventory

def check_inventory():
    with app.app_context():
        inventory_count = Inventory.query.count()
        print(f"\nInventory Records: {inventory_count}")
        
        if inventory_count > 0:
            sample = Inventory.query.first()
            print("\nSample Inventory Record:")
            print(f"Week: {sample.week_commencing}")
            print(f"Item: {sample.item.description if sample.item else 'N/A'}")
            print(f"Category: {sample.category.name if sample.category else 'N/A'}")
            print(f"Price/KG: {sample.price_per_kg}")
            print(f"Required Total Production: {sample.required_total_production}")
            print(f"Value Required RM: {sample.value_required_rm}")
            print(f"Current Stock: {sample.current_stock}")
            print(f"Required for Plan: {sample.required_for_plan}")
            print(f"Variance Week: {sample.variance_week}")
            print(f"KG Required: {sample.kg_required}")
            print(f"Variance: {sample.variance}")
            print(f"To Be Ordered: {sample.to_be_ordered}")
            print(f"Closing Stock: {sample.closing_stock}")

if __name__ == '__main__':
    check_inventory() 