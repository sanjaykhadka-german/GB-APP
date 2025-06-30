#!/usr/bin/env python3
"""
Fix Production Aggregation Script
=================================

This script fixes existing production entries by recalculating them based on 
proper aggregation of packing requirements by production_code.

The issue: Production entries were created with broken logic that didn't properly
aggregate all packing entries that share the same production_code.

The fix: Recalculate all production entries by summing packing requirements 
grouped by production_code for each recipe family and date.
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
from sqlalchemy import func

def fix_production_aggregation_for_week(week_commencing_str, dry_run=True):
    """
    Fix production aggregation for a specific week.
    
    Args:
        week_commencing_str: Week date in YYYY-MM-DD format
        dry_run: If True, only show what would be changed without making changes
    """
    print(f"\n{'='*60}")
    print(f"FIXING PRODUCTION AGGREGATION FOR WEEK: {week_commencing_str}")
    print(f"DRY RUN: {dry_run}")
    print(f"{'='*60}")
    
    try:
        week_commencing = datetime.strptime(week_commencing_str, '%Y-%m-%d').date()
    except ValueError:
        print(f"ERROR: Invalid date format. Use YYYY-MM-DD")
        return False
    
    # Get all packing entries for this week
    packing_entries = Packing.query.filter_by(week_commencing=week_commencing).all()
    
    if not packing_entries:
        print(f"No packing entries found for week {week_commencing}")
        return True
        
    print(f"Found {len(packing_entries)} packing entries for week {week_commencing}")
    
    # Group packing entries by date only (not by recipe family)
    # This allows us to aggregate production codes ACROSS recipe families
    date_groups = {}
    
    for packing in packing_entries:
        date_key = packing.packing_date
        
        if date_key not in date_groups:
            date_groups[date_key] = []
        date_groups[date_key].append(packing)
    
    print(f"Found {len(date_groups)} unique packing dates")
    
    total_fixes_needed = 0
    
    # Process each date group
    for packing_date, packings in date_groups.items():
        print(f"\n--- Processing Date {packing_date} ---")
        
        # Calculate correct production totals by production_code ACROSS ALL recipe families
        production_code_to_total = {}
        production_code_to_packings = {}
        production_code_to_recipe_families = {}
        
        for packing in packings:
            item = ItemMaster.query.filter_by(item_code=packing.product_code).first()
            if item and item.production_code:
                prod_code = item.production_code
                requirement_kg = packing.requirement_kg or 0.0
                recipe_family = packing.product_code.split('.')[0] if '.' in packing.product_code else packing.product_code
                
                if prod_code not in production_code_to_total:
                    production_code_to_total[prod_code] = 0.0
                    production_code_to_packings[prod_code] = []
                    production_code_to_recipe_families[prod_code] = set()
                    
                production_code_to_total[prod_code] += requirement_kg
                production_code_to_packings[prod_code].append(packing.product_code)
                production_code_to_recipe_families[prod_code].add(recipe_family)
                
                print(f"  {packing.product_code}: {requirement_kg} KG → Production Code: {prod_code}")
        
        if not production_code_to_total:
            print(f"  No production codes found for date {packing_date}")
            continue
            
        # Show summary by production code
        for prod_code in production_code_to_total:
            recipe_families = sorted(production_code_to_recipe_families[prod_code])
            print(f"  📊 Production Code {prod_code}: {production_code_to_total[prod_code]} KG from recipe families {', '.join(recipe_families)}")
            
        # Check existing production entries and compare
        for production_code, expected_total in production_code_to_total.items():
            existing_production = Production.query.filter_by(
                production_code=production_code,
                production_date=packing_date,
                week_commencing=week_commencing
            ).first()
            
            batch_size = 100.0
            expected_batches = expected_total / batch_size if expected_total > 0 else 0.0
            
            if existing_production:
                current_total = existing_production.total_kg or 0.0
                current_batches = existing_production.batches or 0.0
                
                if abs(current_total - expected_total) > 0.01:  # Allow for small rounding differences
                    print(f"  ❌ MISMATCH - Production Code {production_code}:")
                    print(f"     Current Total: {current_total} KG (batches: {current_batches})")
                    print(f"     Expected Total: {expected_total} KG (batches: {expected_batches})")
                    print(f"     Difference: {expected_total - current_total} KG")
                    print(f"     Contributing packings: {', '.join(production_code_to_packings[production_code])}")
                    
                    if not dry_run:
                        # Get WIP item for description
                        wip_item = ItemMaster.query.filter_by(item_code=production_code, item_type="WIP").first()
                        description = wip_item.description if wip_item else f"{production_code} - WIP"
                        
                        existing_production.total_kg = expected_total
                        existing_production.batches = expected_batches
                        existing_production.description = description
                        print(f"     ✅ FIXED: Updated to {expected_total} KG")
                    
                    total_fixes_needed += 1
                else:
                    print(f"  ✅ OK - Production Code {production_code}: {current_total} KG (matches expected)")
            else:
                print(f"  ⚠️  MISSING - Production Code {production_code}:")
                print(f"     Expected Total: {expected_total} KG (batches: {expected_batches})")
                print(f"     Contributing packings: {', '.join(production_code_to_packings[production_code])}")
                
                if not dry_run:
                    # Get WIP item for description
                    wip_item = ItemMaster.query.filter_by(item_code=production_code, item_type="WIP").first()
                    description = wip_item.description if wip_item else f"{production_code} - WIP"
                    
                    new_production = Production(
                        production_date=packing_date,
                        production_code=production_code,
                        description=description,
                        batches=expected_batches,
                        total_kg=expected_total,
                        week_commencing=week_commencing
                    )
                    db.session.add(new_production)
                    print(f"     ✅ CREATED: New production entry with {expected_total} KG")
                
                total_fixes_needed += 1
    
    if not dry_run and total_fixes_needed > 0:
        try:
            db.session.commit()
            print(f"\n✅ Successfully applied {total_fixes_needed} fixes to database!")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error applying fixes: {str(e)}")
            return False
    elif dry_run and total_fixes_needed > 0:
        print(f"\n📋 DRY RUN COMPLETE: Found {total_fixes_needed} production entries that need fixing")
        print("Run with dry_run=False to apply the fixes")
    else:
        print(f"\n✅ No fixes needed - all production totals are correct!")
    
    return True

def fix_production_aggregation_all_weeks(dry_run=True):
    """Fix production aggregation for all weeks that have packing data."""
    print(f"\n{'='*60}")
    print(f"FIXING PRODUCTION AGGREGATION FOR ALL WEEKS")
    print(f"{'='*60}")
    
    # Get all unique week_commencing dates from packing table
    weeks = db.session.query(Packing.week_commencing).distinct().filter(
        Packing.week_commencing.isnot(None)
    ).order_by(Packing.week_commencing).all()
    
    if not weeks:
        print("No weeks found with packing data")
        return True
    
    print(f"Found {len(weeks)} weeks with packing data")
    
    success = True
    for (week,) in weeks:
        week_str = week.strftime('%Y-%m-%d')
        result = fix_production_aggregation_for_week(week_str, dry_run)
        if not result:
            success = False
            print(f"Failed to process week {week_str}")
    
    return success

def main():
    """Main function to run the production aggregation fix."""
    app = create_app()
    
    with app.app_context():
        print("Production Aggregation Fix Script")
        print("=" * 50)
        
        # You can specify a specific week or fix all weeks
        if len(sys.argv) > 1:
            week_str = sys.argv[1]
            dry_run = True if len(sys.argv) <= 2 or sys.argv[2] != 'apply' else False
            
            print(f"Fixing specific week: {week_str}")
            success = fix_production_aggregation_for_week(week_str, dry_run)
        else:
            # Default: fix all weeks (dry run first)
            print("Fixing all weeks with packing data...")
            
            # First do a dry run
            print("\n🔍 STEP 1: DRY RUN - Analyzing what needs to be fixed...")
            success = fix_production_aggregation_all_weeks(dry_run=True)
            
            if success:
                response = input("\nDo you want to apply these fixes? (yes/no): ").strip().lower()
                if response in ['yes', 'y']:
                    print("\n🔧 STEP 2: APPLYING FIXES...")
                    success = fix_production_aggregation_all_weeks(dry_run=False)
                else:
                    print("Fixes not applied.")
        
        if success:
            print("\n✅ Script completed successfully!")
        else:
            print("\n❌ Script completed with errors!")
            sys.exit(1)

if __name__ == '__main__':
    main() 