#!/usr/bin/env python3
"""
Fix ItemMaster model by adding missing audit columns.
This resolves the SQLAlchemy relationship error with the User model.
"""

import os

def fix_item_master_model():
    """Add missing audit columns to ItemMaster model."""
    
    # Read the current model
    model_path = "models/item_master.py"
    with open(model_path, 'r') as f:
        content = f.read()
    
    # Check if audit columns already exist
    if 'created_by_id' in content:
        print("✅ Audit columns already exist in ItemMaster model")
        return
    
    # Find the location to insert audit columns (after calculation_factor)
    lines = content.split('\n')
    
    # Find the line with calculation_factor
    insert_index = -1
    for i, line in enumerate(lines):
        if 'calculation_factor' in line and 'db.Column' in line:
            insert_index = i + 1
            break
    
    if insert_index == -1:
        print("❌ Could not find calculation_factor column to insert after")
        return
    
    # Audit columns to insert
    audit_columns = [
        "",
        "    # Audit fields (added to resolve User model relationship errors)",
        "    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)",
        "    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)",
        "    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())",
        "    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())"
    ]
    
    # Insert the audit columns
    for i, column in enumerate(audit_columns):
        lines.insert(insert_index + i, column)
    
    # Write back to file
    new_content = '\n'.join(lines)
    with open(model_path, 'w') as f:
        f.write(new_content)
    
    print("✅ Added missing audit columns to ItemMaster model")
    print("   - created_by_id")
    print("   - updated_by_id") 
    print("   - created_at")
    print("   - updated_at")

def main():
    print("🔧 Fixing ItemMaster model audit columns...")
    fix_item_master_model()
    print("✅ ItemMaster model fix completed!")

if __name__ == "__main__":
    main() 