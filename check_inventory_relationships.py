from app import create_app
from database import db
from models.inventory import Inventory
from models.item_master import ItemMaster

def check_relationships():
    app = create_app()
    with app.app_context():
        print("Checking inventory records...")
        
        # Get all inventory records
        inventories = Inventory.query.all()
        print(f"\nTotal inventory records: {len(inventories)}")
        
        # Check each inventory record
        for inv in inventories:
            print(f"\nInventory ID: {inv.id}")
            print(f"Item ID: {inv.item_id}")
            
            # Try to get the related item
            item = ItemMaster.query.get(inv.item_id)
            if item:
                print(f"Found related item: {item.description}")
            else:
                print(f"WARNING: No item found for item_id {inv.item_id}")

if __name__ == '__main__':
    check_relationships() 