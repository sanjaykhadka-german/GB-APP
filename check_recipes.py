#!/usr/bin/env python3
"""
Check Recipe Master Table
========================

This script checks the recipe master table and its relationships.
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_recipes():
    """Check recipe master table and relationships."""
    try:
        # Count total recipes
        recipe_count = RecipeMaster.query.count()
        logger.info(f"Total recipes: {recipe_count}")

        # Get all WIP items
        wip_items = ItemMaster.query.join(ItemType).filter(ItemType.type_name == 'WIP').all()
        logger.info(f"Total WIP items: {len(wip_items)}")

        # Check recipes for each WIP item
        for wip in wip_items:
            # Check recipes where this WIP is used as a component
            used_in = RecipeMaster.query.filter_by(component_item_id=wip.id).count()
            logger.info(f"WIP {wip.item_code} is used as component in {used_in} recipes")

            # Check recipes where this WIP is the recipe WIP
            has_components = RecipeMaster.query.filter_by(recipe_wip_id=wip.id).count()
            logger.info(f"WIP {wip.item_code} has {has_components} components in its recipe")

        # Get all WIPF items
        wipf_items = ItemMaster.query.join(ItemType).filter(ItemType.type_name == 'WIPF').all()
        logger.info(f"Total WIPF items: {len(wipf_items)}")

        # Check recipes for each WIPF item
        for wipf in wipf_items:
            # Check recipes where this WIPF is used as a component
            used_in = RecipeMaster.query.filter_by(component_item_id=wipf.id).count()
            logger.info(f"WIPF {wipf.item_code} is used as component in {used_in} recipes")

            # Check recipes where this WIPF is the recipe WIP
            has_components = RecipeMaster.query.filter_by(recipe_wip_id=wipf.id).count()
            logger.info(f"WIPF {wipf.item_code} has {has_components} components in its recipe")

        # Get all FG items
        fg_items = ItemMaster.query.join(ItemType).filter(ItemType.type_name == 'FG').all()
        logger.info(f"Total FG items: {len(fg_items)}")

        # Check recipes for each FG item
        for fg in fg_items:
            # Check recipes where this FG is used as a component
            used_in = RecipeMaster.query.filter_by(component_item_id=fg.id).count()
            logger.info(f"FG {fg.item_code} is used as component in {used_in} recipes")

            # Check recipes where this FG is the recipe WIP
            has_components = RecipeMaster.query.filter_by(recipe_wip_id=fg.id).count()
            logger.info(f"FG {fg.item_code} has {has_components} components in its recipe")

    except Exception as e:
        logger.error(f"Error checking recipes: {str(e)}")
        raise e

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        check_recipes() 