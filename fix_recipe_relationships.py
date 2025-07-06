#!/usr/bin/env python3
"""
Fix Recipe Relationships
=======================

This script fixes recipe relationships between FG, WIP, and WIPF items.
"""

import sys
import os
from datetime import datetime
import logging

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from database import db
from models.recipe_master import RecipeMaster
from models.item_master import ItemMaster
from models.item_type import ItemType
from models.packing import Packing

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_relationships():
    try:
        # Get all items
        items = ItemMaster.query.all()
        
        # Create a dictionary to store items by code for faster lookup
        items_by_code = {item.item_code: item for item in items}
        
        # Track changes
        updates = 0
        
        for item in items:
            if not item.item_code:
                continue
                
            # Get item type
            item_type = item.item_type.type_name if item.item_type else None
            
            if item_type == 'FG':
                # For FG items, find their WIP and WIPF components
                base_code = item.item_code.split('.')[0]
                
                # Look for WIP (base code only)
                wip_code = base_code
                wip_item = items_by_code.get(wip_code)
                
                if wip_item and wip_item.item_type and wip_item.item_type.type_name == 'WIP':
                    if item.wip_item_id != wip_item.id:
                        logger.info(f"Setting WIP relationship: {item.item_code} -> {wip_item.item_code}")
                        item.wip_item_id = wip_item.id
                        updates += 1
                
                # Look for WIPF (base code with potential variations)
                possible_wipf_codes = [
                    f"{base_code}.56",  # Common format for frankfurters
                    f"{base_code}.100",  # Common format for 100g products
                    f"{base_code}.125",  # Common format for 125g products
                    f"{base_code}.165",  # Common format for 165g products
                ]
                
                for wipf_code in possible_wipf_codes:
                    wipf_item = items_by_code.get(wipf_code)
                    if wipf_item and wipf_item.item_type and wipf_item.item_type.type_name == 'WIPF':
                        if item.wipf_item_id != wipf_item.id:
                            logger.info(f"Setting WIPF relationship: {item.item_code} -> {wipf_item.item_code}")
                            item.wipf_item_id = wipf_item.id
                            updates += 1
                        break  # Found the WIPF, no need to check other formats
            
            elif item_type == 'WIPF':
                # For WIPF items, find their WIP component
                base_code = item.item_code.split('.')[0]
                
                # Look for WIP
                wip_code = base_code
                wip_item = items_by_code.get(wip_code)
                
                if wip_item and wip_item.item_type and wip_item.item_type.type_name == 'WIP':
                    if item.wip_item_id != wip_item.id:
                        logger.info(f"Setting WIP relationship for WIPF: {item.item_code} -> {wip_item.item_code}")
                        item.wip_item_id = wip_item.id
                        updates += 1
        
        if updates > 0:
            db.session.commit()
            logger.info(f"Updated {updates} relationships")
        else:
            logger.info("No relationships needed updating")
            
        return True, f"Updated {updates} relationships"
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error fixing relationships: {str(e)}")
        return False, str(e)

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        success, message = fix_relationships()
        print(message) 