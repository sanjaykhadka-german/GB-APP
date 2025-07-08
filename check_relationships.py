from app import create_app, db
from models.item_master import ItemMaster
from models.item_type import ItemType
from models.packing import Packing
from models.recipe_master import RecipeMaster

def check_relationships():
    """Check item relationships in the database"""
    # Get all packing entries
    packing_entries = Packing.query.all()
    print(f"\nFound {len(packing_entries)} packing entries")
    
    for packing in packing_entries:
        print(f"\nPacking Entry {packing.id}:")
        print(f"- FG Code: {packing.item.item_code if packing.item else 'No item'}")
        print(f"- Week Commencing: {packing.week_commencing}")
        print(f"- Requirement KG: {packing.requirement_kg}")
        
        if packing.item:
            print("\nItem Relationships:")
            print(f"- WIP Item: {packing.item.wip_item.item_code if packing.item.wip_item else 'None'}")
            print(f"- WIPF Item: {packing.item.wipf_item.item_code if packing.item.wipf_item else 'None'}")
            
            if packing.item.wip_item:
                recipes = RecipeMaster.query.filter_by(recipe_wip_id=packing.item.wip_item_id).all()
                print(f"\nRecipes for WIP ({len(recipes)} found):")
                for recipe in recipes:
                    component = ItemMaster.query.get(recipe.component_item_id)
                    print(f"- Component: {component.item_code if component else 'Not found'}")
                    print(f"  Quantity: {recipe.quantity_kg}kg")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        check_relationships() 