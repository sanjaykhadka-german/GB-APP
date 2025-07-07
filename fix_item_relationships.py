from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models.item_master import ItemMaster
from models.item_type import ItemType
from app import app, db

def setup_relationships():
    with app.app_context():
        print("Setting up FG item relationships...")
        
        # Get all item types
        fg_type = ItemType.query.filter_by(type_name='FG').first()
        wip_type = ItemType.query.filter_by(type_name='WIP').first()
        wipf_type = ItemType.query.filter_by(type_name='WIPF').first()
        
        if not all([fg_type, wip_type, wipf_type]):
            print("Error: Missing required item types")
            return
        
        # Get all FG items
        fg_items = ItemMaster.query.filter_by(item_type_id=fg_type.id).all()
        
        for fg in fg_items:
            print(f"\nProcessing FG: {fg.item_code}")
            
            # Extract base code (remove last segment)
            base_code = '.'.join(fg.item_code.split('.')[:-1]) if '.' in fg.item_code else fg.item_code
            
            # Find corresponding WIP
            wip = ItemMaster.query.filter(
                ItemMaster.item_type_id == wip_type.id,
                ItemMaster.item_code.like(f"{base_code}%")
            ).first()
            
            if wip:
                print(f"Found WIP: {wip.item_code}")
                fg.wip_item_id = wip.id
            
            # Find corresponding WIPF
            wipf = ItemMaster.query.filter(
                ItemMaster.item_type_id == wipf_type.id,
                ItemMaster.item_code.like(f"{base_code}.6%")  # WIPF items usually have .6xxx suffix
            ).first()
            
            if wipf:
                print(f"Found WIPF: {wipf.item_code}")
                fg.wipf_item_id = wipf.id
        
        # Commit changes
        try:
            db.session.commit()
            print("\nSuccessfully updated relationships")
        except Exception as e:
            db.session.rollback()
            print(f"\nError saving relationships: {str(e)}")

if __name__ == '__main__':
    setup_relationships() 