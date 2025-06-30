#!/usr/bin/env python3
"""
Test Special Order Production Update
===================================

This script tests that when special orders are updated, the production entries
are properly recalculated using cross-recipe-family aggregation.
"""

import sys
import os
from datetime import datetime, date

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models.production import Production
from models.packing import Packing  
from models.item_master import ItemMaster

def test_special_order_production_update():
    """Test that special order updates trigger proper production recalculation."""
    print("🧪 Testing Special Order Production Update")
    print("=" * 50)
    
    # Test configuration
    week_commencing = date(2025, 6, 30)
    packing_date = date(2025, 6, 30)
    
    print(f"Testing for week: {week_commencing}")
    
    # Step 1: Get current production total for code 1003
    current_production = Production.query.filter_by(
        production_code='1003',
        production_date=packing_date,
        week_commencing=week_commencing
    ).first()
    
    if not current_production:
        print("❌ No production entry found for code 1003")
        return False
        
    print(f"📊 Current Production Code 1003: {current_production.total_kg} KG")
    
    # Step 2: Get current packing entries that contribute to production code 1003
    all_packings = Packing.query.filter_by(
        week_commencing=week_commencing,
        packing_date=packing_date
    ).all()
    
    production_1003_packings = []
    total_requirement_kg = 0.0
    
    for packing in all_packings:
        item = ItemMaster.query.filter_by(item_code=packing.product_code).first()
        if item and item.production_code == '1003':
            production_1003_packings.append(packing)
            total_requirement_kg += (packing.requirement_kg or 0.0)
            print(f"  {packing.product_code}: {packing.requirement_kg} KG (Special Order: {packing.special_order_kg or 0} KG)")
    
    print(f"📋 Total calculated from packings: {total_requirement_kg} KG")
    print(f"📊 Current production entry: {current_production.total_kg} KG")
    
    # Step 3: Check if they match
    if abs(total_requirement_kg - current_production.total_kg) < 0.01:
        print("✅ Production and packing totals MATCH!")
        return True
    else:
        difference = total_requirement_kg - current_production.total_kg
        print(f"❌ Production and packing totals DO NOT MATCH!")
        print(f"   Difference: {difference} KG")
        print(f"   This suggests that special order updates are not triggering production recalculation")
        return False

def show_production_breakdown():
    """Show detailed breakdown of production codes and their contributing packings."""
    print("\n🔍 Detailed Production Breakdown")
    print("=" * 50)
    
    week_commencing = date(2025, 6, 30)
    packing_date = date(2025, 6, 30)
    
    # Get all packings for this date
    all_packings = Packing.query.filter_by(
        week_commencing=week_commencing,
        packing_date=packing_date
    ).all()
    
    # Group by production code
    production_code_to_packings = {}
    
    for packing in all_packings:
        item = ItemMaster.query.filter_by(item_code=packing.product_code).first()
        if item and item.production_code:
            prod_code = item.production_code
            if prod_code not in production_code_to_packings:
                production_code_to_packings[prod_code] = []
            production_code_to_packings[prod_code].append(packing)
    
    # Show breakdown for each production code
    for prod_code in sorted(production_code_to_packings.keys()):
        packings = production_code_to_packings[prod_code]
        
        # Calculate total from packings
        total_from_packings = sum(p.requirement_kg or 0.0 for p in packings)
        
        # Get production entry
        production = Production.query.filter_by(
            production_code=prod_code,
            production_date=packing_date,
            week_commencing=week_commencing
        ).first()
        
        production_total = production.total_kg if production else 0.0
        
        print(f"\n📦 Production Code: {prod_code}")
        print(f"   Production Entry: {production_total} KG")
        print(f"   Packing Total: {total_from_packings} KG")
        
        if abs(total_from_packings - production_total) < 0.01:
            print(f"   ✅ MATCH")
        else:
            print(f"   ❌ MISMATCH (Diff: {total_from_packings - production_total} KG)")
        
        print(f"   Contributing packings:")
        for packing in packings:
            special_order = packing.special_order_kg or 0.0
            recipe_family = packing.product_code.split('.')[0]
            print(f"     - {packing.product_code} (Recipe {recipe_family}): {packing.requirement_kg} KG (Special: {special_order} KG)")

if __name__ == "__main__":
    # Create Flask app context
    app = create_app()
    with app.app_context():
        print("🚀 Special Order Production Update Test")
        print("=" * 60)
        
        # Run tests
        result = test_special_order_production_update()
        
        # Show detailed breakdown
        show_production_breakdown()
        
        print("\n" + "=" * 60)
        if result:
            print("🎉 TEST PASSED: Production aggregation is working correctly!")
        else:
            print("🔧 TEST ISSUE: Production aggregation may need attention")
            print("💡 Try updating a special order in the UI and check if production totals update")
        
        print("✅ Test completed!") 