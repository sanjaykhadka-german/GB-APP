#!/usr/bin/env python3
"""
Test script to verify inventory database updates when production planned values change.
"""

from app import app, db
from models import Production, Inventory, ItemMaster
from populate_inventory import get_daily_required_kg
from datetime import datetime, date

def test_inventory_update():
    """Test if inventory updates when production planned values change."""
    
    with app.app_context():
        # Get a specific week for testing - use the week that has data
        test_week = date(2025, 6, 16)  # Monday, June 16, 2025
        
        print(f"Testing inventory update for week: {test_week}")
        
        # Get all production records for this week
        productions = Production.query.filter_by(week_commencing=test_week).all()
        print(f"Found {len(productions)} production records for this week")
        
        # Get all inventory records for this week
        inventory_records = Inventory.query.filter_by(week_commencing=test_week).all()
        print(f"Found {len(inventory_records)} inventory records for this week")
        
        # Show current production planned values
        print("\nCurrent Production Planned Values:")
        for prod in productions:
            print(f"  Production {prod.id}: {prod.production_code}")
            print(f"    Monday: {prod.monday_planned}")
            print(f"    Tuesday: {prod.tuesday_planned}")
            print(f"    Wednesday: {prod.wednesday_planned}")
            print(f"    Thursday: {prod.thursday_planned}")
            print(f"    Friday: {prod.friday_planned}")
            print(f"    Saturday: {prod.saturday_planned}")
            print(f"    Sunday: {prod.sunday_planned}")
        
        # Show current inventory required kg values
        print("\nCurrent Inventory Required KG Values:")
        for inv in inventory_records:
            print(f"  Inventory {inv.id}: {inv.item.description if inv.item else 'Unknown'}")
            print(f"    Monday: {inv.monday_required_kg}")
            print(f"    Tuesday: {inv.tuesday_required_kg}")
            print(f"    Wednesday: {inv.wednesday_required_kg}")
            print(f"    Thursday: {inv.thursday_required_kg}")
            print(f"    Friday: {inv.friday_required_kg}")
            print(f"    Saturday: {inv.saturday_required_kg}")
            print(f"    Sunday: {inv.sunday_required_kg}")
        
        # Test the get_daily_required_kg function for a specific raw material
        if inventory_records:
            test_rm_id = inventory_records[0].item_id
            print(f"\nTesting get_daily_required_kg for raw material ID: {test_rm_id}")
            
            daily_reqs = get_daily_required_kg(db.session, test_week, test_rm_id)
            print(f"Calculated daily requirements: {daily_reqs}")
            
            # Update one production record's tuesday_planned value
            if productions:
                test_prod = productions[0]
                old_tuesday = test_prod.tuesday_planned
                new_tuesday = old_tuesday + 100.0 if old_tuesday else 100.0
                
                print(f"\nUpdating production {test_prod.id} tuesday_planned from {old_tuesday} to {new_tuesday}")
                test_prod.tuesday_planned = new_tuesday
                db.session.commit()
                
                # Recalculate daily requirements
                new_daily_reqs = get_daily_required_kg(db.session, test_week, test_rm_id)
                print(f"New calculated daily requirements: {new_daily_reqs}")
                
                # Check if Tuesday value changed
                if new_daily_reqs[1] != daily_reqs[1]:
                    print(f"✅ SUCCESS: Tuesday required kg changed from {daily_reqs[1]} to {new_daily_reqs[1]}")
                else:
                    print(f"❌ FAILED: Tuesday required kg did not change (still {daily_reqs[1]})")
                
                # Revert the change
                test_prod.tuesday_planned = old_tuesday
                db.session.commit()
                print(f"Reverted tuesday_planned back to {old_tuesday}")

if __name__ == "__main__":
    test_inventory_update() 