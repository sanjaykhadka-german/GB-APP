from app import create_app, db
from models.packing import Packing
from models.item_master import ItemMaster
from models.recipe_master import RecipeMaster

def check_packing():
    """Check packing entries and their relationships"""
    # Get all packing entries
    packing_entries = Packing.query.all()
    print(f"\nFound {len(packing_entries)} packing entries")
    
    for packing in packing_entries:
        print(f"\nPacking Entry {packing.id}:")
        print(f"- FG Code: {packing.item.item_code if packing.item else 'No item'}")
        print(f"- Week Commencing: {packing.week_commencing}")
        print(f"- Requirement KG: {packing.requirement_kg}")
        print(f"- Department ID: {packing.department_id}")
        print(f"- Machinery ID: {packing.machinery_id}")
        
        if packing.item:
            print("\nItem Relationships:")
            print(f"- WIP Item: {packing.item.wip_item.item_code if packing.item.wip_item else 'None'}")
            print(f"- WIPF Item: {packing.item.wipf_item.item_code if packing.item.wipf_item else 'None'}")
            
            if packing.item.wip_item:
                print(f"\nWIP Item Details:")
                print(f"- Department ID: {packing.item.wip_item.department_id}")
                print(f"- Machinery ID: {packing.item.wip_item.machinery_id}")
                
                recipes = RecipeMaster.query.filter_by(recipe_wip_id=packing.item.wip_item_id).all()
                print(f"\nRecipes for WIP ({len(recipes)} found):")
                for recipe in recipes:
                    component = ItemMaster.query.get(recipe.component_item_id)
                    print(f"- Component: {component.item_code if component else 'Not found'}")
                    print(f"  Quantity: {recipe.quantity_kg}kg")
            
            if packing.item.wipf_item:
                print(f"\nWIPF Item Details:")
                print(f"- Department ID: {packing.item.wipf_item.department_id}")
                print(f"- Machinery ID: {packing.item.wipf_item.machinery_id}")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        check_packing() 