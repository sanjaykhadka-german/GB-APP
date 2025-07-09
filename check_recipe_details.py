from app import app
from database import db
from models.recipe_master import RecipeMaster
from models.item_master import ItemMaster
from models.item_type import ItemType

def check_recipe_details():
    with app.app_context():
        # Get sample recipe
        sample = RecipeMaster.query.first()
        if sample:
            print("\nSample Recipe Details:")
            print(f"Recipe WIP ID: {sample.recipe_wip_id}")
            print(f"Component ID: {sample.component_item_id}")
            print(f"Recipe WIP: {sample.recipe_wip.item_code} - {sample.recipe_wip.description}")
            print(f"Component: {sample.component_item.item_code} - {sample.component_item.description}")
            print(f"Quantity: {sample.quantity_kg}")
            
            # Get item types
            rm_type = ItemType.query.filter_by(type_name='RM').first()
            wip_type = ItemType.query.filter_by(type_name='WIP').first()
            
            if rm_type and wip_type:
                print(f"\nItem Types:")
                print(f"RM Type ID: {rm_type.id}")
                print(f"WIP Type ID: {wip_type.id}")
                
                # Check recipe WIP item type
                print(f"\nRecipe WIP Item Type: {sample.recipe_wip.item_type_id}")
                print(f"Component Item Type: {sample.component_item.item_type_id}")
                
                # Get all recipes where component is a raw material
                rm_recipes = RecipeMaster.query.join(
                    ItemMaster,
                    RecipeMaster.component_item_id == ItemMaster.id
                ).filter(
                    ItemMaster.item_type_id == rm_type.id
                ).all()
                
                print(f"\nRecipes with RM components: {len(rm_recipes)}")
                for recipe in rm_recipes[:5]:  # Show first 5
                    print(f"- {recipe.recipe_wip.item_code} uses {recipe.component_item.item_code}")

if __name__ == '__main__':
    check_recipe_details() 