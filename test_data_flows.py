#!/usr/bin/env python3
"""
Comprehensive Test Script for Data Flow Scenarios
================================================

This script tests all the data flow scenarios described in the documentation:
1. SOH upload flow
2. Manual SOH entry flow
3. Manual packing entry flow
4. Special order KG scenarios

To run this test, ensure you have the Flask app and database configured.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import date, datetime, timedelta
from app import app
from database import db
from models.soh import SOH
from models.packing import Packing
from models.filling import Filling
from models.production import Production
from models.item_master import ItemMaster
from models.usage_report_table import UsageReportTable
from models.raw_material_report_table import RawMaterialReportTable
from models.inventory import Inventory
from controllers.soh_controller import create_packing_entry_from_soh
from controllers.packing_controller import update_packing_entry, re_aggregate_filling_and_production_for_week
from controllers.bom_service import BOMService

def print_header(title):
    """Print a formatted header for test sections."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_subheader(title):
    """Print a formatted subheader for test subsections."""
    print(f"\n{'─'*40}")
    print(f"  {title}")
    print(f"{'─'*40}")

def setup_test_data():
    """Set up basic test data if it doesn't exist."""
    print_header("SETTING UP TEST DATA")
    
    # Check if test items exist
    test_items = [
        {'item_code': '2015.100.2', 'description': 'Test FG Item 1', 'avg_weight_per_unit': 2.5, 'max_level': 500, 'min_level': 100},
        {'item_code': '2015.125.02', 'description': 'Test FG Item 2', 'avg_weight_per_unit': 3.0, 'max_level': 300, 'min_level': 50},
        {'item_code': '2015.100', 'description': 'Test WIPF Item', 'avg_weight_per_unit': 2.5, 'max_level': 1000, 'min_level': 200},
        {'item_code': '2015', 'description': 'Test WIP Item', 'avg_weight_per_unit': 2.5, 'max_level': 2000, 'min_level': 400},
    ]
    
    items_created = 0
    for item_data in test_items:
        existing_item = ItemMaster.query.filter_by(item_code=item_data['item_code']).first()
        if not existing_item:
            item = ItemMaster(
                item_code=item_data['item_code'],
                description=item_data['description'],
                avg_weight_per_unit=item_data['avg_weight_per_unit'],
                max_level=item_data['max_level'],
                min_level=item_data['min_level']
            )
            db.session.add(item)
            items_created += 1
            print(f"Created test item: {item_data['item_code']}")
    
    if items_created > 0:
        db.session.commit()
        print(f"Created {items_created} test items")
    else:
        print("Test items already exist")

def test_soh_upload_flow():
    """Test Scenario 1: SOH Upload Flow."""
    print_header("TEST 1: SOH UPLOAD FLOW")
    
    # Test data
    item_code = "2015.100.2"
    week_commencing = date(2024, 1, 1)  # Monday
    soh_units = 150
    special_order_kg = 100
    
    print(f"Testing SOH upload for item: {item_code}")
    print(f"Week commencing: {week_commencing}")
    print(f"SOH units: {soh_units}")
    print(f"Special order KG: {special_order_kg}")
    
    # Get item
    item = ItemMaster.query.filter_by(item_code=item_code).first()
    if not item:
        print(f"ERROR: Item {item_code} not found")
        return
    
    # Clean up existing data for this test
    SOH.query.filter_by(item_id=item.id, week_commencing=week_commencing).delete()
    Packing.query.filter_by(item_id=item.id, week_commencing=week_commencing).delete()
    db.session.commit()
    
    print_subheader("Step 1: Create SOH Entry")
    
    # Create SOH entry (simulating upload)
    soh = SOH(
        item_id=item.id,
        week_commencing=week_commencing,
        soh_total_units=soh_units,
        soh_total_boxes=soh_units / 10,  # Assuming 10 units per box
        description=item.description
    )
    db.session.add(soh)
    db.session.commit()
    print(f"✓ Created SOH entry: {soh_units} units")
    
    print_subheader("Step 2: Create Packing Entry from SOH")
    
    # Create packing entry from SOH (simulating the automatic process)
    try:
        packing = create_packing_entry_from_soh(item_code, item.description, week_commencing, soh_units, item)
        db.session.commit()
        print(f"✓ Created packing entry:")
        print(f"  - SOH requirement units/week: {packing.soh_requirement_units_week}")
        print(f"  - Requirement KG: {packing.requirement_kg}")
        print(f"  - Requirement units: {packing.requirement_unit}")
    except Exception as e:
        print(f"✗ Error creating packing entry: {e}")
        return
    
    print_subheader("Step 3: Add Special Order")
    
    # Update packing with special order
    try:
        success, message = update_packing_entry(
            item_code, 
            item.description, 
            packing_date=week_commencing,
            special_order_kg=special_order_kg,
            avg_weight_per_unit=item.avg_weight_per_unit,
            week_commencing=week_commencing
        )
        
        if success:
            # Reload packing to see updated values
            packing = Packing.query.filter_by(item_id=item.id, week_commencing=week_commencing).first()
            print(f"✓ Updated packing with special order:")
            print(f"  - Special order KG: {packing.special_order_kg}")
            print(f"  - Updated requirement KG: {packing.requirement_kg}")
            print(f"  - Updated requirement units: {packing.requirement_unit}")
        else:
            print(f"✗ Failed to update packing: {message}")
    except Exception as e:
        print(f"✗ Error updating packing: {e}")
        return
    
    print_subheader("Step 4: Trigger Downstream Updates")
    
    # Trigger downstream updates
    try:
        success, message = re_aggregate_filling_and_production_for_week(week_commencing)
        if success:
            print(f"✓ Successfully triggered downstream updates")
            
            # Check for filling entries
            filling_entries = Filling.query.filter_by(week_commencing=week_commencing).all()
            print(f"  - Created {len(filling_entries)} filling entries")
            
            # Check for production entries
            production_entries = Production.query.filter_by(week_commencing=week_commencing).all()
            print(f"  - Created {len(production_entries)} production entries")
            
        else:
            print(f"✗ Failed downstream updates: {message}")
    except Exception as e:
        print(f"✗ Error in downstream updates: {e}")

def test_manual_soh_entry():
    """Test Scenario 2: Manual SOH Entry Flow."""
    print_header("TEST 2: MANUAL SOH ENTRY FLOW")
    
    # Test data
    item_code = "2015.125.02"
    week_commencing = date(2024, 1, 8)  # Monday
    soh_units = 200
    soh_boxes = 20
    
    print(f"Testing manual SOH entry for item: {item_code}")
    print(f"Week commencing: {week_commencing}")
    print(f"SOH units: {soh_units}")
    print(f"SOH boxes: {soh_boxes}")
    
    # Get item
    item = ItemMaster.query.filter_by(item_code=item_code).first()
    if not item:
        print(f"ERROR: Item {item_code} not found")
        return
    
    # Clean up existing data
    SOH.query.filter_by(item_id=item.id, week_commencing=week_commencing).delete()
    Packing.query.filter_by(item_id=item.id, week_commencing=week_commencing).delete()
    db.session.commit()
    
    print_subheader("Step 1: Manual SOH Creation")
    
    # Create SOH entry manually
    soh = SOH(
        item_id=item.id,
        week_commencing=week_commencing,
        soh_total_units=soh_units,
        soh_total_boxes=soh_boxes,
        description=item.description,
        edit_date=datetime.now()
    )
    db.session.add(soh)
    db.session.commit()
    print(f"✓ Created manual SOH entry: {soh_units} units, {soh_boxes} boxes")
    
    print_subheader("Step 2: Automatic Packing Creation")
    
    # Create packing from SOH
    try:
        packing = create_packing_entry_from_soh(item_code, item.description, week_commencing, soh_units, item)
        db.session.commit()
        print(f"✓ Automatic packing creation:")
        print(f"  - SOH requirement calculated: {packing.soh_requirement_units_week} units")
        print(f"  - Requirement KG: {packing.requirement_kg}")
        print(f"  - Current SOH KG: {packing.soh_kg}")
        print(f"  - Total stock KG: {packing.total_stock_kg}")
    except Exception as e:
        print(f"✗ Error in automatic packing creation: {e}")

def test_manual_packing_entry():
    """Test Scenario 3: Manual Packing Entry Flow."""
    print_header("TEST 3: MANUAL PACKING ENTRY FLOW")
    
    # Test data
    item_code = "2015.100.2"
    packing_date = date(2024, 1, 15)
    week_commencing = date(2024, 1, 15)  # Monday
    special_order_kg = 75
    requirement_kg = 500
    requirement_unit = 200
    
    print(f"Testing manual packing entry for item: {item_code}")
    print(f"Packing date: {packing_date}")
    print(f"Week commencing: {week_commencing}")
    print(f"Special order KG: {special_order_kg}")
    print(f"Requirement KG: {requirement_kg}")
    
    # Get item
    item = ItemMaster.query.filter_by(item_code=item_code).first()
    if not item:
        print(f"ERROR: Item {item_code} not found")
        return
    
    # Clean up existing data
    Packing.query.filter_by(item_id=item.id, week_commencing=week_commencing).delete()
    db.session.commit()
    
    print_subheader("Step 1: Manual Packing Creation")
    
    # Create packing entry manually
    packing = Packing(
        item_id=item.id,
        packing_date=packing_date,
        week_commencing=week_commencing,
        special_order_kg=special_order_kg,
        requirement_kg=requirement_kg,
        requirement_unit=requirement_unit,
        avg_weight_per_unit=item.avg_weight_per_unit
    )
    db.session.add(packing)
    db.session.commit()
    print(f"✓ Created manual packing entry:")
    print(f"  - Special order KG: {packing.special_order_kg}")
    print(f"  - Requirement KG: {packing.requirement_kg}")
    print(f"  - Requirement units: {packing.requirement_unit}")
    
    print_subheader("Step 2: Trigger Downstream Creation")
    
    # Trigger downstream updates
    try:
        success, message = re_aggregate_filling_and_production_for_week(week_commencing)
        if success:
            print(f"✓ Downstream creation successful")
            
            # Check results
            filling_count = Filling.query.filter_by(week_commencing=week_commencing).count()
            production_count = Production.query.filter_by(week_commencing=week_commencing).count()
            
            print(f"  - Filling entries created: {filling_count}")
            print(f"  - Production entries created: {production_count}")
        else:
            print(f"✗ Downstream creation failed: {message}")
    except Exception as e:
        print(f"✗ Error in downstream creation: {e}")

def test_special_order_scenarios():
    """Test Scenario 4: Special Order KG Scenarios."""
    print_header("TEST 4: SPECIAL ORDER KG SCENARIOS")
    
    item_code = "2015.100.2"
    week_commencing = date(2024, 1, 22)  # Monday
    
    # Get item
    item = ItemMaster.query.filter_by(item_code=item_code).first()
    if not item:
        print(f"ERROR: Item {item_code} not found")
        return
    
    # Clean up existing data
    Packing.query.filter_by(item_id=item.id, week_commencing=week_commencing).delete()
    db.session.commit()
    
    print_subheader("Scenario 4.1: Direct Special Order Addition")
    
    # Create base packing entry
    base_requirement_units = 100
    special_order_kg = 50
    
    try:
        success, message = update_packing_entry(
            item_code,
            item.description,
            packing_date=week_commencing,
            special_order_kg=special_order_kg,
            avg_weight_per_unit=item.avg_weight_per_unit,
            soh_requirement_units_week=base_requirement_units,
            week_commencing=week_commencing
        )
        
        if success:
            packing = Packing.query.filter_by(item_id=item.id, week_commencing=week_commencing).first()
            base_kg = base_requirement_units * item.avg_weight_per_unit
            expected_total = base_kg + special_order_kg
            
            print(f"✓ Direct special order addition:")
            print(f"  - Base requirement: {base_requirement_units} units × {item.avg_weight_per_unit} kg/unit = {base_kg} kg")
            print(f"  - Special order: {special_order_kg} kg")
            print(f"  - Expected total: {expected_total} kg")
            print(f"  - Actual total: {packing.requirement_kg} kg")
            print(f"  - Match: {'✓' if abs(packing.requirement_kg - expected_total) < 0.1 else '✗'}")
        else:
            print(f"✗ Failed: {message}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print_subheader("Scenario 4.2: Bulk Edit Special Order")
    
    # Test bulk edit scenario (simulated)
    try:
        packing = Packing.query.filter_by(item_id=item.id, week_commencing=week_commencing).first()
        if packing:
            # Simulate bulk edit calculation
            soh_kg = 100  # Simulated current SOH
            total_stock_kg = 500  # Simulated total stock needed
            new_special_order = 75
            
            # Apply bulk edit formula
            old_requirement = packing.requirement_kg
            packing.special_order_kg = new_special_order
            packing.requirement_kg = round(total_stock_kg - soh_kg + packing.special_order_kg, 0)
            
            db.session.commit()
            
            print(f"✓ Bulk edit special order:")
            print(f"  - Total stock needed: {total_stock_kg} kg")
            print(f"  - Current SOH: {soh_kg} kg")
            print(f"  - New special order: {new_special_order} kg")
            print(f"  - Formula: {total_stock_kg} - {soh_kg} + {new_special_order} = {packing.requirement_kg} kg")
            print(f"  - Old requirement: {old_requirement} kg")
            print(f"  - New requirement: {packing.requirement_kg} kg")
        else:
            print("✗ No packing entry found for bulk edit test")
    except Exception as e:
        print(f"✗ Error in bulk edit test: {e}")
    
    print_subheader("Scenario 4.3: Inline Edit Special Order")
    
    # Test inline edit scenario
    try:
        packing = Packing.query.filter_by(item_id=item.id, week_commencing=week_commencing).first()
        if packing:
            # Simulate inline edit
            new_special_order = 125
            old_requirement = packing.requirement_kg
            
            # Apply inline edit (similar to bulk edit formula)
            packing.special_order_kg = new_special_order
            
            # Recalculate using the inline edit formula
            avg_weight_per_unit = item.avg_weight_per_unit
            soh_units = 40  # Simulated SOH units
            soh_kg = round(soh_units * avg_weight_per_unit, 0)
            total_stock_kg = 500  # Simulated total stock
            
            packing.requirement_kg = round(total_stock_kg - soh_kg + packing.special_order_kg, 0)
            
            db.session.commit()
            
            print(f"✓ Inline edit special order:")
            print(f"  - New special order: {new_special_order} kg")
            print(f"  - Old requirement: {old_requirement} kg")
            print(f"  - New requirement: {packing.requirement_kg} kg")
            print(f"  - Formula: {total_stock_kg} - {soh_kg} + {new_special_order} = {packing.requirement_kg} kg")
        else:
            print("✗ No packing entry found for inline edit test")
    except Exception as e:
        print(f"✗ Error in inline edit test: {e}")

def test_data_integrity():
    """Test data integrity across all tables."""
    print_header("TEST 5: DATA INTEGRITY CHECK")
    
    # Check relationships and data consistency
    print_subheader("Checking Data Relationships")
    
    try:
        # Check packing to filling relationships
        packing_count = Packing.query.count()
        filling_count = Filling.query.count()
        production_count = Production.query.count()
        usage_count = UsageReportTable.query.count()
        
        print(f"Current data state:")
        print(f"  - Packing entries: {packing_count}")
        print(f"  - Filling entries: {filling_count}")
        print(f"  - Production entries: {production_count}")
        print(f"  - Usage report entries: {usage_count}")
        
        # Check for orphaned entries
        orphaned_packings = Packing.query.filter(Packing.item_id.is_(None)).count()
        orphaned_fillings = Filling.query.filter(Filling.item_id.is_(None)).count()
        
        print(f"Orphaned entries:")
        print(f"  - Orphaned packings: {orphaned_packings}")
        print(f"  - Orphaned fillings: {orphaned_fillings}")
        
        # Check requirement calculations
        packings_with_special_orders = Packing.query.filter(Packing.special_order_kg > 0).all()
        print(f"Packings with special orders: {len(packings_with_special_orders)}")
        
        for packing in packings_with_special_orders:
            print(f"  - {packing.item.item_code}: Special={packing.special_order_kg}kg, Requirement={packing.requirement_kg}kg")
            
    except Exception as e:
        print(f"✗ Error in data integrity check: {e}")

def main():
    """Run all test scenarios."""
    print("COMPREHENSIVE DATA FLOW TESTING")
    print("===============================")
    print("This script will test all data flow scenarios in the system.")
    print("Make sure you have a test database configured!")
    print()
    
    try:
        with app.app_context():
            # Setup test data
            setup_test_data()
            
            # Run all test scenarios
            test_soh_upload_flow()
            test_manual_soh_entry()
            test_manual_packing_entry()
            test_special_order_scenarios()
            test_data_integrity()
            
            print_header("TESTING COMPLETE")
            print("All test scenarios have been executed.")
            print("Review the output above for any errors or issues.")
            
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()