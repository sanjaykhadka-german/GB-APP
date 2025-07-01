#!/usr/bin/env python3
"""
Fix Filling Totals Script
=================================

This script fixes filling totals by re-running the aggregation for a specific date.
"""

from app import create_app
from controllers.packing_controller import re_aggregate_filling_and_production_for_date
from datetime import datetime

def main():
    """Main function to run the filling totals fix."""
    app = create_app()
    
    with app.app_context():
        print("Filling Totals Fix Script")
        print("=" * 50)
        
        # Fix specific date
        date_str = '2025-06-30'
        fix_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        week_commencing = fix_date  # For this case, the date is Monday
        
        print(f"\nFixing filling totals for date: {date_str}")
        print(f"Week commencing: {week_commencing}")
        
        try:
            re_aggregate_filling_and_production_for_date(fix_date, week_commencing)
            print("✅ Successfully fixed filling totals!")
        except Exception as e:
            print(f"❌ Error fixing filling totals: {str(e)}")
            return False
            
        return True

if __name__ == '__main__':
    success = main()
    if not success:
        exit(1) 