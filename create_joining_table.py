#!/usr/bin/env python3
"""
Create Joining Table Migration Script
====================================

This script creates the joining table for FG → WIPF → WIP relationships
to optimize BOM calculations and SOH processing.
"""

import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_joining_table():
    """Create the joining table and populate initial data"""
    
    print("Starting joining table creation...")
    
    try:
        from database import db
        from app import app
        from models.joining import Joining
        from models.item_master import ItemMaster
        from models.item_type import ItemType
        
        print("✓ Imports successful")
        
        with app.app_context():
            try:
                # Create the table
                print("Creating database tables...")
                db.create_all()
                print("✓ Joining table created successfully")
                
                # Check if we have any existing data to migrate
                fg_items = db.session.query(ItemMaster).join(ItemType).filter(ItemType.type_name == 'FG').all()
                print(f"Found {len(fg_items)} FG items in system")
                
                # Create some example joining records based on existing pattern
                example_joinings = [
                    {
                        'fg_code': '2045.123.14',
                        'filling_code': '1002',
                        'production_code': None,
                        'weekly_average': 1000.0,
                        'calculation_factor': 1.0
                    },
                    {
                        'fg_code': '9004.11',
                        'filling_code': None,
                        'production_code': '1003',
                        'weekly_average': 500.0,
                        'calculation_factor': 1.0
                    }
                ]
                
                created_count = 0
                for example in example_joinings:
                    print(f"Processing joining record for {example['fg_code']}...")
                    
                    # Check if FG item exists
                    fg_item = ItemMaster.query.filter_by(item_code=example['fg_code']).first()
                    if not fg_item:
                        print(f"⚠ FG item {example['fg_code']} not found, skipping...")
                        continue
                    
                    # Check if already exists
                    existing = Joining.query.filter_by(fg_code=example['fg_code']).first()
                    if existing:
                        print(f"⚠ Joining record for {example['fg_code']} already exists, skipping...")
                        continue
                    
                    # Get filling item if specified
                    filling_item = None
                    if example['filling_code']:
                        filling_item = ItemMaster.query.filter_by(item_code=example['filling_code']).first()
                        if not filling_item:
                            print(f"⚠ Filling item {example['filling_code']} not found for {example['fg_code']}")
                    
                    # Get production item if specified
                    production_item = None
                    if example['production_code']:
                        production_item = ItemMaster.query.filter_by(item_code=example['production_code']).first()
                        if not production_item:
                            print(f"⚠ Production item {example['production_code']} not found for {example['fg_code']}")
                    
                    # Create joining record
                    joining = Joining(
                        fg_code=example['fg_code'],
                        fg_description=fg_item.description,
                        filling_code=example['filling_code'],
                        filling_description=filling_item.description if filling_item else None,
                        production_code=example['production_code'],
                        production_description=production_item.description if production_item else None,
                        fg_item_id=fg_item.id,
                        filling_item_id=filling_item.id if filling_item else None,
                        production_item_id=production_item.id if production_item else None,
                        weekly_average=example['weekly_average'],
                        calculation_factor=example['calculation_factor']
                    )
                    
                    db.session.add(joining)
                    created_count += 1
                    print(f"✓ Created joining record for {example['fg_code']}")
                
                # Commit all changes
                print("Committing changes to database...")
                db.session.commit()
                print(f"✓ Created {created_count} joining records")
                
                # Verify the table
                total_records = Joining.query.count()
                print(f"✓ Total joining records in database: {total_records}")
                
                # Display some sample records
                sample_records = Joining.query.limit(5).all()
                if sample_records:
                    print("\nSample joining records:")
                    for record in sample_records:
                        flow_type = record.get_manufacturing_flow_type()
                        print(f"  {record.fg_code} → {record.filling_code or 'None'} → {record.production_code or 'None'} ({flow_type})")
                
                print("\n✅ Joining table migration completed successfully!")
                
            except Exception as e:
                db.session.rollback()
                print(f"❌ Error during database operations: {str(e)}")
                import traceback
                traceback.print_exc()
                raise
                
    except Exception as e:
        print(f"❌ Error creating joining table: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == '__main__':
    create_joining_table() 