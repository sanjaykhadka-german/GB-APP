from app import app
from database import db
from models.recipe_master import RecipeMaster
from models.item_master import ItemMaster
from models.item_type import ItemType

def check_recipe_data():
    with app.app_context():
        # Get counts
        recipe_count = RecipeMaster.query.count()
        print(f"\nTotal recipes: {recipe_count}")
        
        # Get sample recipe
        sample = RecipeMaster.query.first()
        if sample:
            print("\nSample recipe:")
            print(f"Product: {sample.recipe_wip.description if sample.recipe_wip else 'N/A'}")
            print(f"Component: {sample.component_item.description if sample.component_item else 'N/A'}")
            print(f"Quantity: {sample.quantity_kg}")
        
        # Get RM type ID
        rm_type = ItemType.query.filter_by(type_name='RM').first()
        if rm_type:
            # Get raw materials used in recipes
            raw_materials_in_recipes = db.session.query(ItemMaster).join(
                RecipeMaster, RecipeMaster.component_item_id == ItemMaster.id
            ).filter(
                ItemMaster.item_type_id == rm_type.id
            ).distinct().all()
            
            print(f"\nRaw materials used in recipes: {len(raw_materials_in_recipes)}")
            for rm in raw_materials_in_recipes[:5]:  # Show first 5
                print(f"- {rm.item_code} - {rm.description}")
            
            # Get products in recipes
            products_in_recipes = db.session.query(ItemMaster).join(
                RecipeMaster, RecipeMaster.recipe_wip_id == ItemMaster.id
            ).distinct().all()
            
            print(f"\nProducts in recipes: {len(products_in_recipes)}")
            for prod in products_in_recipes[:5]:  # Show first 5
                print(f"- {prod.item_code} - {prod.description}")
            
            # Get recipes per raw material
            print("\nRecipes per raw material:")
            for rm in raw_materials_in_recipes[:5]:  # Show first 5
                recipe_count = RecipeMaster.query.filter_by(component_item_id=rm.id).count()
                print(f"- {rm.item_code}: {recipe_count} recipes")

if __name__ == '__main__':
    check_recipe_data() 