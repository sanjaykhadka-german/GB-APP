from database import db
from models.item_master import ItemMaster
from models.item_type import ItemType
from models.recipe_master import RecipeMaster
from app import app

def check_item_relationships():
    with app.app_context():
        # Get all WIP items
        wip_items = ItemMaster.query.join(ItemMaster.item_type).filter(
            ItemType.type_name == 'WIP'
        ).all()
        
        print("\nChecking WIP items and their relationships:")
        print("-" * 80)
        
        for wip in wip_items:
            print(f"\nWIP Item: {wip.item_code} - {wip.description}")
            
            # Get FG items that use this WIP
            fg_items = ItemMaster.query.filter(ItemMaster.wip_component == wip).all()
            if fg_items:
                print("Used by FG items:")
                for fg in fg_items:
                    print(f"  - {fg.item_code} - {fg.description}")
            else:
                print("  No FG items linked to this WIP")
                
            # Get recipe components for this WIP
            recipes = RecipeMaster.query.filter_by(recipe_wip_id=wip.id).all()
            if recipes:
                print("Recipe components:")
                for recipe in recipes:
                    component = recipe.component_item
                    if component:
                        print(f"  - {component.item_code} ({component.item_type.type_name}) - {component.description}")
            else:
                print("  No recipe components found")
                
        # Get all WIPF items
        wipf_items = ItemMaster.query.join(ItemMaster.item_type).filter(
            ItemType.type_name == 'WIPF'
        ).all()
        
        print("\nChecking WIPF items and their relationships:")
        print("-" * 80)
        
        for wipf in wipf_items:
            print(f"\nWIPF Item: {wipf.item_code} - {wipf.description}")
            
            # Get FG items that use this WIPF
            fg_items = ItemMaster.query.filter(ItemMaster.wipf_component == wipf).all()
            if fg_items:
                print("Used by FG items:")
                for fg in fg_items:
                    print(f"  - {fg.item_code} - {fg.description}")
            else:
                print("  No FG items linked to this WIPF")
                
            # Get recipe components for this WIPF
            recipes = RecipeMaster.query.filter_by(recipe_wip_id=wipf.id).all()
            if recipes:
                print("Recipe components:")
                for recipe in recipes:
                    component = recipe.component_item
                    if component:
                        print(f"  - {component.item_code} ({component.item_type.type_name}) - {component.description}")
            else:
                print("  No recipe components found")

if __name__ == '__main__':
    check_item_relationships() 