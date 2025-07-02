#!/usr/bin/env python3
"""
Import Joining Data to Joining Table
====================================

This script imports existing joining relationships from joining_export.xlsx
into the new joining table for optimized BOM calculations.
"""

import sys
import os
import pandas as pd

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def import_joining_data():
    """Import joining data from Excel file to database"""
    
    print("Starting joining data import...")
    
    try:
        from database import db
        from app import app
        from models.joining import Joining
        from models.item_master import ItemMaster
        from models.item_type import ItemType
        
        print("✓ Imports successful")
        
        with app.app_context():
            try:
                # Check if joining_export.xlsx exists
                excel_file = 'joining_export.xlsx'
                if not os.path.exists(excel_file):
                    print(f"❌ File {excel_file} not found")
                    return
                
                print(f"Reading data from {excel_file}...")
                df = pd.read_excel(excel_file, sheet_name='Joining')  # Correct sheet name
                
                print(f"Found {len(df)} rows in Excel file")
                print("Columns:", list(df.columns))
                
                # Clean up column names
                df.columns = df.columns.str.strip()
                
                # Expected columns based on actual file structure
                required_columns = ['fg_code', 'filling_code', 'production', 'description']
                
                # Check if all required columns exist
                missing_cols = [col for col in required_columns if col not in df.columns]
                if missing_cols:
                    print(f"❌ Missing columns: {missing_cols}")
                    print(f"Available columns: {list(df.columns)}")
                    return
                
                # Get current item counts for reference
                fg_items = db.session.query(ItemMaster).join(ItemType).filter(ItemType.type_name == 'FG').all()
                wipf_items = db.session.query(ItemMaster).join(ItemType).filter(ItemType.type_name == 'WIPF').all()
                wip_items = db.session.query(ItemMaster).join(ItemType).filter(ItemType.type_name == 'WIP').all()
                
                print(f"Current system has: {len(fg_items)} FG, {len(wipf_items)} WIPF, {len(wip_items)} WIP items")
                
                # Statistics
                processed = 0
                created = 0
                skipped = 0
                errors = []
                
                for index, row in df.iterrows():
                    try:
                        fg_code = str(row['fg_code']).strip()
                        filling_code = str(row['filling_code']).strip() if pd.notnull(row['filling_code']) else None
                        production_code = str(row['production']).strip() if pd.notnull(row['production']) else None
                        description = str(row['description']).strip() if pd.notnull(row['description']) else ''
                        
                        # Skip if FG code is empty or NaN
                        if not fg_code or fg_code.lower() in ['nan', 'none', '']:
                            continue
                        
                        # Clean up codes - remove 'nan' strings
                        if filling_code and filling_code.lower() in ['nan', 'none', '']:
                            filling_code = None
                        if production_code and production_code.lower() in ['nan', 'none', '']:
                            production_code = None
                        
                        print(f"Processing: {fg_code} → {filling_code} → {production_code}")
                        
                        # Check if FG item exists in ItemMaster
                        fg_item = ItemMaster.query.filter_by(item_code=fg_code).first()
                        if not fg_item:
                            errors.append(f"FG item {fg_code} not found in ItemMaster")
                            continue
                        
                        # Check if joining record already exists
                        existing_joining = Joining.query.filter_by(fg_code=fg_code).first()
                        if existing_joining:
                            print(f"  ⚠ Joining record for {fg_code} already exists, skipping...")
                            skipped += 1
                            continue
                        
                        # Get filling item if specified
                        filling_item = None
                        filling_description = None
                        if filling_code:
                            filling_item = ItemMaster.query.filter_by(item_code=filling_code).first()
                            if filling_item:
                                filling_description = filling_item.description
                            else:
                                print(f"  ⚠ Filling item {filling_code} not found in ItemMaster")
                        
                        # Get production item if specified
                        production_item = None
                        production_description = None
                        if production_code:
                            production_item = ItemMaster.query.filter_by(item_code=production_code).first()
                            if production_item:
                                production_description = production_item.description
                            else:
                                print(f"  ⚠ Production item {production_code} not found in ItemMaster")
                        
                        # Create joining record
                        joining = Joining(
                            fg_code=fg_code,
                            fg_description=fg_item.description,
                            filling_code=filling_code,
                            filling_description=filling_description,
                            production_code=production_code,
                            production_description=production_description,
                            fg_item_id=fg_item.id,
                            filling_item_id=filling_item.id if filling_item else None,
                            production_item_id=production_item.id if production_item else None,
                            weekly_average=0.0,  # Default value, can be updated later
                            calculation_factor=1.0  # Default value
                        )
                        
                        db.session.add(joining)
                        created += 1
                        flow_type = joining.get_manufacturing_flow_type()
                        print(f"  ✓ Created: {fg_code} ({flow_type})")
                        
                        processed += 1
                        
                        # Commit in batches
                        if processed % 10 == 0:
                            db.session.commit()
                            print(f"  Committed batch... ({processed} processed)")
                        
                    except Exception as e:
                        error_msg = f"Error processing row {index}: {str(e)}"
                        print(f"  ❌ {error_msg}")
                        errors.append(error_msg)
                
                # Final commit
                print("Performing final commit...")
                db.session.commit()
                
                # Summary
                print("\n" + "="*60)
                print("IMPORT SUMMARY")
                print("="*60)
                print(f"Total rows processed: {processed}")
                print(f"Records created: {created}")
                print(f"Records skipped: {skipped}")
                print(f"Errors: {len(errors)}")
                
                if errors:
                    print("\nErrors encountered:")
                    for error in errors[:10]:  # Show first 10 errors
                        print(f"  - {error}")
                    if len(errors) > 10:
                        print(f"  ... and {len(errors) - 10} more errors")
                
                # Verify final state
                total_joining_records = Joining.query.count()
                print(f"\nTotal joining records in database: {total_joining_records}")
                
                # Show flow type distribution
                flow_types = {}
                all_joinings = Joining.query.all()
                for j in all_joinings:
                    flow_type = j.get_manufacturing_flow_type()
                    flow_types[flow_type] = flow_types.get(flow_type, 0) + 1
                
                print("\nFlow type distribution:")
                for flow_type, count in flow_types.items():
                    print(f"  {flow_type}: {count}")
                
                print("\n✅ Joining data import completed successfully!")
                
            except Exception as e:
                db.session.rollback()
                print(f"❌ Error during import: {str(e)}")
                import traceback
                traceback.print_exc()
                raise
                
    except Exception as e:
        print(f"❌ Error importing joining data: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == '__main__':
    import_joining_data() 