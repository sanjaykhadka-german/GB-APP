from app import app
from models.inventory import Inventory

def check_inventory():
    with app.app_context():
        print("Checking inventory records...")
        
        # Get total count
        total_count = Inventory.query.count()
        print(f"\nTotal inventory records: {total_count}")
        
        # Get sample records
        print("\nSample records:")
        for record in Inventory.query.limit(5).all():
            print(f"\n{record.item.item_code} - {record.item.description}:")
            print(f"  Week Commencing: {record.week_commencing}")
            print(f"  Required Total: {record.required_total}")
            print(f"  Current Stock: {record.current_stock}")
            print(f"  Value Required: {record.value_required}")
            print(f"  Required for Plan: {record.required_for_plan}")
            print(f"  Variance: {record.variance}")

if __name__ == '__main__':
    check_inventory() 