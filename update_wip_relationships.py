"""
Update WIP relationships in item_master table
Copies wip_component_id to wip_item_id for WIPF items
"""
from app import app, db
from models.item_master import ItemMaster
from models.item_type import ItemType
from sqlalchemy import text

def update_wip_relationships():
    try:
        # Get all WIPF items
        wipf_items = ItemMaster.query.join(
            ItemType, ItemMaster.item_type_id == ItemType.id
        ).filter(
            ItemType.type_name == 'WIPF'
        ).all()
        
        print(f"Found {len(wipf_items)} WIPF items")
        
        # Update each WIPF item
        for item in wipf_items:
            if item.wip_component_id:
                print(f"Updating {item.item_code}: wip_component_id={item.wip_component_id}")
                # Execute raw SQL to update the wip_item_id column
                sql = text("UPDATE item_master SET wip_item_id = :wip_id WHERE id = :item_id")
                db.session.execute(sql, {"wip_id": item.wip_component_id, "item_id": item.id})
                print(f"Updated {item.item_code}")
        
        # Commit changes
        db.session.commit()
        print("Successfully updated WIP relationships")
        
    except Exception as e:
        print(f"Error updating relationships: {str(e)}")
        db.session.rollback()

if __name__ == '__main__':
    with app.app_context():
        update_wip_relationships() 