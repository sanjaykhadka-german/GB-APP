#!/usr/bin/env python3
"""
Check Packing Items
==================

This script checks the item types of packing items.
"""

import sys
import os
from datetime import datetime
import logging

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from database import db
from models.packing import Packing
from models.item_master import ItemMaster
from models.item_type import ItemType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_packing_items():
    """Check item types of packing items."""
    try:
        # Get all packing entries
        packing_entries = Packing.query.all()
        logger.info(f"Total packing entries: {len(packing_entries)}")

        # Group by item type
        item_type_counts = {}
        for packing in packing_entries:
            item = packing.item
            if not item:
                logger.warning(f"No item found for packing {packing.id}")
                continue

            item_type = item.item_type.type_name if item.item_type else "Unknown"
            if item_type not in item_type_counts:
                item_type_counts[item_type] = {
                    'count': 0,
                    'total_kg': 0,
                    'items': set()
                }
            
            item_type_counts[item_type]['count'] += 1
            item_type_counts[item_type]['total_kg'] += packing.requirement_kg or 0
            item_type_counts[item_type]['items'].add(item.item_code)

        # Print summary
        logger.info("\nPacking Items by Type:")
        for item_type, data in item_type_counts.items():
            logger.info(f"\nType: {item_type}")
            logger.info(f"Count: {data['count']} entries")
            logger.info(f"Total KG: {data['total_kg']}")
            logger.info("Items:")
            for item_code in sorted(data['items']):
                logger.info(f"  - {item_code}")

    except Exception as e:
        logger.error(f"Error checking packing items: {str(e)}")
        raise e

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        check_packing_items() 