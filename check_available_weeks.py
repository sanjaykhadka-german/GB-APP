#!/usr/bin/env python3
"""
Check what weeks have production and inventory data.
"""

from app import app, db
from models import Production, Inventory
from sqlalchemy import func
from datetime import datetime

def check_available_weeks():
    """Check what weeks have data."""
    
    with app.app_context():
        # Get all unique weeks from production
        production_weeks = db.session.query(Production.week_commencing).distinct().all()
        production_weeks = [week[0] for week in production_weeks]
        
        # Get all unique weeks from inventory
        inventory_weeks = db.session.query(Inventory.week_commencing).distinct().all()
        inventory_weeks = [week[0] for week in inventory_weeks]
        
        print("Production weeks:")
        for week in production_weeks:
            count = Production.query.filter_by(week_commencing=week).count()
            print(f"  {week}: {count} records")
        
        print("\nInventory weeks:")
        for week in inventory_weeks:
            count = Inventory.query.filter_by(week_commencing=week).count()
            print(f"  {week}: {count} records")
        
        # Find common weeks
        common_weeks = set(production_weeks) & set(inventory_weeks)
        print(f"\nCommon weeks with both production and inventory data: {len(common_weeks)}")
        for week in sorted(common_weeks):
            print(f"  {week}")

if __name__ == "__main__":
    check_available_weeks() 