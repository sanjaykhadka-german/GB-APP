#!/usr/bin/env python3
"""
Remove WIPF entries from recipe_master table for specific recipe codes
"""

from app import create_app
from database import db
from models.recipe_master import RecipeMaster
from models.item_master import ItemMaster
from models.item_type import ItemType

def remove_wipf_recipes():
    """Remove WIPF entries from recipe_master for specified recipe codes"""
    app = create_app()
    
    with app.app_context():
        # Recipe codes to process
        recipe_codes = ['1004', '1024', '2002', '2006', '2015', '2045', '2205']
        
        # Get WIPF item type
        wipf_type = ItemType.query.filter_by(type_name='WIPF').first()
        if not wipf_type:
            print("Error: WIPF item type not found")
            return
            
        print("Removing WIPF entries from recipe_master table...")
        
        for recipe_code in recipe_codes:
            print(f"\nProcessing recipe code: {recipe_code}")
            
            # Get the WIP item for this recipe code
            wip_item = ItemMaster.query.filter_by(item_code=recipe_code).first()
            if not wip_item:
                print(f"Warning: No item found with code {recipe_code}")
                continue
                
            # Find recipes where component is WIPF type
            wipf_recipes = RecipeMaster.query.join(
                ItemMaster,
                RecipeMaster.component_item_id == ItemMaster.id
            ).filter(
                ItemMaster.item_type_id == wipf_type.id,
                RecipeMaster.recipe_wip_id == wip_item.id
            ).all()
            
            if wipf_recipes:
                print(f"Found {len(wipf_recipes)} WIPF entries to remove")
                for recipe in wipf_recipes:
                    print(f"- Removing recipe: {recipe.component_item.item_code} from {recipe.recipe_wip.item_code}")
                    db.session.delete(recipe)
            else:
                print("No WIPF entries found")
        
        # Commit the changes
        try:
            db.session.commit()
            print("\nSuccessfully removed WIPF entries from recipe_master table")
        except Exception as e:
            db.session.rollback()
            print(f"\nError removing WIPF entries: {str(e)}")

if __name__ == '__main__':
    remove_wipf_recipes() 