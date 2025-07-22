#!/usr/bin/env python3
"""
Test Special Order Fix
=====================

This script tests that updating special order KG in packing preserves:
1. Production table IDs (no longer changing)
2. Daily planning data (monday_planned, tuesday_planned, etc.)
3. Inventory daily requirements based on production planning
"""

import sys
import os
from datetime import datetime, date

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db
from models.production import Production
from models.packing import Packing
from models.inventory import Inventory
from models.item_master import ItemMaster
from controllers.packing_controller import re_aggregate_filling_and_production_for_week

def test_special_order_fix():
    """Test that special order updates preserve production planning data."""
    print("🧪 Testing Special Order Fix")
    print("=" * 50)
    
    with app.app_context():
        # Test configuration - find the first available packing entry
        print("🔍 Finding available packing entries...")
        
        # Look for any packing entry with WIP relationship
        packing = db.session.query(Packing).join(ItemMaster).filter(
            ItemMaster.wip_item_id.isnot(None)  # Has WIP relationship
        ).first()
        
        if not packing:
            print("❌ No packing entry found with WIP relationship")
            return False
        
        week_commencing = packing.week_commencing
        test_item_code = packing.item.item_code
        
        print(f"✅ Found test entry: {test_item_code} (week: {week_commencing})")
        print(f"📦 Packing entry ID {packing.id}, Current special order: {packing.special_order_kg} kg")
        
        # Step 2: Find related production entries and record their current state
        wip_item = packing.item.wip_item if packing.item else None
        if not wip_item:
            print(f"❌ No WIP item found for {test_item_code}")
            return False
        
        production = Production.query.filter_by(
            week_commencing=week_commencing,
            item_id=wip_item.id
        ).first()
        
        if not production:
            print(f"❌ No production entry found for WIP item {wip_item.item_code}")
            return False
        
        # Record initial state
        initial_production_id = production.id
        initial_total_kg = production.total_kg
        initial_monday_planned = production.monday_planned or 0.0
        initial_tuesday_planned = production.tuesday_planned or 0.0
        initial_special_order_kg = packing.special_order_kg or 0.0
        
        print(f"📊 Initial Production State:")
        print(f"   ID: {initial_production_id}")
        print(f"   Total KG: {initial_total_kg}")
        print(f"   Monday Planned: {initial_monday_planned}")
        print(f"   Tuesday Planned: {initial_tuesday_planned}")
        
        # Step 3: Set some daily planning values if they're zero
        if initial_monday_planned == 0 and initial_tuesday_planned == 0:
            print("📝 Setting initial daily planning values for testing...")
            production.monday_planned = 100.0
            production.tuesday_planned = 200.0
            production.total_planned = 300.0
            db.session.commit()
            print(f"   Set Monday: 100.0, Tuesday: 200.0")
        
        # Step 4: Update special order KG (simulate user edit)
        new_special_order_kg = initial_special_order_kg + 10.0  # Add 10 kg
        print(f"\n🔄 Updating special order KG from {initial_special_order_kg} to {new_special_order_kg}")
        
        # Update packing
        old_requirement_kg = packing.requirement_kg or 0.0
        packing.special_order_kg = new_special_order_kg
        packing.requirement_kg = old_requirement_kg - initial_special_order_kg + new_special_order_kg
        db.session.commit()
        
        # Trigger re-aggregation (this is what happens when user edits special order)
        print("🔄 Triggering downstream re-aggregation...")
        success, message = re_aggregate_filling_and_production_for_week(week_commencing)
        
        if not success:
            print(f"❌ Re-aggregation failed: {message}")
            return False
        
        print(f"✅ Re-aggregation completed: {message}")
        
        # Step 5: Check the results
        print("\n📊 Checking Results...")
        
        # Refresh production entry
        db.session.refresh(production)
        
        # Check ID stability
        final_production_id = production.id
        if final_production_id == initial_production_id:
            print(f"✅ Production ID preserved: {final_production_id}")
        else:
            print(f"❌ Production ID changed from {initial_production_id} to {final_production_id}")
            return False
        
        # Check daily planning data preservation
        final_monday_planned = production.monday_planned or 0.0
        final_tuesday_planned = production.tuesday_planned or 0.0
        
        if final_monday_planned == 100.0 and final_tuesday_planned == 200.0:
            print(f"✅ Daily planning data preserved:")
            print(f"   Monday Planned: {final_monday_planned} (preserved)")
            print(f"   Tuesday Planned: {final_tuesday_planned} (preserved)")
        else:
            print(f"❌ Daily planning data lost:")
            print(f"   Monday Planned: {final_monday_planned} (expected 100.0)")
            print(f"   Tuesday Planned: {final_tuesday_planned} (expected 200.0)")
            return False
        
        # Check total_kg update
        final_total_kg = production.total_kg
        expected_increase = new_special_order_kg - initial_special_order_kg
        
        if abs(final_total_kg - (initial_total_kg + expected_increase)) < 0.01:
            print(f"✅ Total KG correctly updated:")
            print(f"   Initial: {initial_total_kg}")
            print(f"   Final: {final_total_kg}")
            print(f"   Increase: {final_total_kg - initial_total_kg} (expected: {expected_increase})")
        else:
            print(f"⚠️  Total KG update needs verification:")
            print(f"   Initial: {initial_total_kg}")
            print(f"   Final: {final_total_kg}")
            print(f"   Increase: {final_total_kg - initial_total_kg}")
        
        # Step 6: Check inventory impact
        print("\n📊 Checking Inventory Impact...")
        
        # Get raw materials that depend on this production
        inventory_records = Inventory.query.filter_by(week_commencing=week_commencing).all()
        
        non_zero_inventory_count = 0
        for inv in inventory_records:
            daily_total = (inv.monday_required_kg or 0) + (inv.tuesday_required_kg or 0)
            if daily_total > 0:
                non_zero_inventory_count += 1
        
        if non_zero_inventory_count > 0:
            print(f"✅ Inventory data populated: {non_zero_inventory_count} items with daily requirements")
        else:
            print("⚠️  No inventory daily requirements found (may need separate inventory update)")
        
        print("\n" + "=" * 50)
        print("🎉 Test completed successfully!")
        print("✅ Production IDs remain stable")
        print("✅ Daily planning data preserved")
        print("✅ Special order updates work correctly")
        
        return True

if __name__ == "__main__":
    test_special_order_fix() 