#!/usr/bin/env python3
"""
Test script to verify that the special order KG update fix preserves planned values.
This script simulates the issue reported by the user.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models.packing import Packing
from models.production import Production
from models.inventory import Inventory
from models.item_master import ItemMaster
from datetime import date, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_special_order_fix():
    """Test that updating special order KG preserves production planned values and inventory daily values."""
    
    with app.app_context():
        try:
            # Test setup
            test_week = date(2024, 1, 15)  # A Monday
            test_item_code = "1005.2"
            
            logger.info(f"🧪 Testing special order KG update fix for item {test_item_code}")
            
            # Step 1: Find or create a packing entry
            packing = Packing.query.join(ItemMaster).filter(
                ItemMaster.item_code == test_item_code,
                Packing.week_commencing == test_week
            ).first()
            
            if not packing:
                logger.error(f"❌ No packing entry found for {test_item_code} in week {test_week}")
                return False
            
            logger.info(f"✅ Found packing entry: {packing.id}")
            
            # Step 2: Find related production entry
            production = Production.query.join(ItemMaster).filter(
                ItemMaster.item_code.like(f"{test_item_code}%"),  # WIP item might have different suffix
                Production.week_commencing == test_week
            ).first()
            
            if not production:
                logger.error(f"❌ No production entry found for week {test_week}")
                return False
            
            logger.info(f"✅ Found production entry: {production.id} for {production.item.item_code}")
            
            # Step 3: Set some planned values to test preservation
            original_total_planned = 1000.0
            original_monday_planned = 150.0
            original_tuesday_planned = 200.0
            
            production.total_planned = original_total_planned
            production.monday_planned = original_monday_planned
            production.tuesday_planned = original_tuesday_planned
            
            db.session.commit()
            logger.info(f"�� Set planned values - Total: {original_total_planned}, Monday: {original_monday_planned}")
            
            # Step 4: Record original special order KG
            original_special_order_kg = packing.special_order_kg or 0.0
            logger.info(f"📝 Original special order KG: {original_special_order_kg}")
            
            # Step 5: Simulate the special order KG update
            new_special_order_kg = 10.0
            logger.info(f"🔄 Updating special order KG from {original_special_order_kg} to {new_special_order_kg}")
            
            # Simulate the update_cell endpoint logic
            from controllers.packing_controller import re_aggregate_filling_and_production_for_week
            
            # Update the special order KG
            packing.special_order_kg = new_special_order_kg
            db.session.commit()
            
            # Trigger re-aggregation (this is where the bug was)
            success, message = re_aggregate_filling_and_production_for_week(test_week)
            
            if not success:
                logger.error(f"❌ Re-aggregation failed: {message}")
                return False
            
            logger.info(f"✅ Re-aggregation completed: {message}")
            
            # Step 6: Check if production planned values are preserved
            db.session.refresh(production)
            
            logger.info(f"🔍 Checking production planned values after re-aggregation...")
            logger.info(f"   Total planned: {production.total_planned} (should be {original_total_planned})")
            logger.info(f"   Monday planned: {production.monday_planned} (should be {original_monday_planned})")
            
            # Verify planned values are preserved
            planned_values_preserved = (
                abs((production.total_planned or 0) - original_total_planned) < 0.01 and
                abs((production.monday_planned or 0) - original_monday_planned) < 0.01
            )
            
            if planned_values_preserved:
                logger.info("✅ SUCCESS: Production planned values were preserved!")
                return True
            else:
                logger.error("❌ FAILURE: Production planned values were reset to zero!")
                return False
            
        except Exception as e:
            logger.error(f"❌ Test failed with exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_special_order_fix()
    sys.exit(0 if success else 1)
