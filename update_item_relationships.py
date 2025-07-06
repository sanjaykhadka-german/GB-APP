from app import db, create_app
from models.item_master import ItemMaster
from models.item_type import ItemType
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_base_code(item_code):
    """Get the base code (before the first dot) from an item code."""
    return item_code.split('.')[0] if item_code else None

def get_filling_code(item_code):
    """Get the filling code (first two parts) from an item code."""
    parts = item_code.split('.')
    return f"{parts[0]}.{parts[1]}" if len(parts) > 1 else None

def update_relationships():
    app = create_app()
    with app.app_context():
        try:
            # Get all items
            items = ItemMaster.query.all()
            
            # Create dictionaries for faster lookup
            items_by_code = {item.item_code: item for item in items}
            wip_items = {}  # Base code -> WIP item
            wipf_items = {}  # Filling code -> WIPF item
            
            # First pass: Identify WIP and WIPF items
            for item in items:
                if not item.item_code:
                    continue
                    
                item_type = item.item_type.type_name if item.item_type else None
                
                if item_type == 'WIP':
                    base_code = get_base_code(item.item_code)
                    if base_code:
                        wip_items[base_code] = item
                elif item_type == 'WIPF':
                    base_code = get_base_code(item.item_code)
                    if base_code:
                        wipf_items[base_code] = item
            
            # Second pass: Update relationships for FG items
            updates = 0
            for item in items:
                if not item.item_code:
                    continue
                    
                item_type = item.item_type.type_name if item.item_type else None
                
                if item_type == 'FG':
                    base_code = get_base_code(item.item_code)
                    filling_code = get_filling_code(item.item_code)
                    
                    # Find corresponding WIP and WIPF items
                    wip_item = wip_items.get(base_code)
                    wipf_item = wipf_items.get(base_code)
                    
                    if wip_item and item.wip_item_id != wip_item.id:
                        item.wip_item_id = wip_item.id
                        updates += 1
                        logger.info(f"Updated WIP relationship for {item.item_code} -> {wip_item.item_code}")
                    
                    if wipf_item and item.wipf_item_id != wipf_item.id:
                        item.wipf_item_id = wipf_item.id
                        updates += 1
                        logger.info(f"Updated WIPF relationship for {item.item_code} -> {wipf_item.item_code}")
            
            if updates > 0:
                db.session.commit()
                logger.info(f"Successfully updated {updates} relationships")
            else:
                logger.info("No relationships needed updating")
                
        except Exception as e:
            logger.error(f"Error updating relationships: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    update_relationships() 