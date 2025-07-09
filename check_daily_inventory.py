"""
Script to check daily inventory data
"""
from app import app
from database import db
from models.inventory import Inventory

def check_daily_inventory():
    with app.app_context():
        try:
            print("Checking daily inventory data...")
            
            # Get all inventory records
            inventories = Inventory.query.limit(10).all()
            print(f"Found {len(inventories)} inventory records (showing first 10)")
            
            for inv in inventories:
                print(f"\n{inv.item.description}")
                print(f"Week: {inv.week_commencing}")
                print(f"Required Total: {inv.required_total_production}")
                print(f"Daily breakdown:")
                print(f"  Monday: {inv.monday}")
                print(f"  Tuesday: {inv.tuesday}")
                print(f"  Wednesday: {inv.wednesday}")
                print(f"  Thursday: {inv.thursday}")
                print(f"  Friday: {inv.friday}")
                print(f"  Saturday: {inv.saturday}")
                print(f"  Sunday: {inv.sunday}")
                
                # Calculate weekly total
                weekly_total = inv.calculate_weekly_total()
                print(f"  Weekly total: {weekly_total}")
                print(f"  Matches required: {abs(float(inv.required_total_production) - weekly_total) < 0.01}")
                
                if len(inventories) <= 3:  # Show details for first 3 only
                    continue
                else:
                    print("...")
                    break
            
            print(f"\nTotal inventory records: {Inventory.query.count()}")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    check_daily_inventory() 