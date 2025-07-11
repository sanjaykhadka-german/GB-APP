from app import app
from database import db
from models.item_master import ItemMaster
from models.item_type import ItemType
from models.raw_material_stocktake import RawMaterialStocktake

def check_raw_materials():
    with app.app_context():
        try:
            print("Checking raw materials in the database...")
            
            # Get RM type
            rm_type = ItemType.query.filter_by(type_name='RM').first()
            if not rm_type:
                print("Error: RM item type not found")
                return
                
            print(f"\nFound RM type with ID: {rm_type.id}")
            
            # Get all raw materials
            raw_materials = ItemMaster.query.filter_by(item_type_id=rm_type.id).all()
            print(f"\nFound {len(raw_materials)} raw materials in ItemMaster")
            
            if raw_materials:
                print("\nSample raw materials:")
                for rm in raw_materials[:5]:
                    print(f"  - {rm.item_code}: {rm.description}")
            
            # Get all stocktake items
            stocktake_items = db.session.query(RawMaterialStocktake.item_code).distinct().all()
            stocktake_codes = [item[0] for item in stocktake_items]
            print(f"\nFound {len(stocktake_codes)} unique item codes in RawMaterialStocktake")
            
            # Check which stocktake items don't have corresponding raw materials
            missing_items = []
            for code in stocktake_codes:
                item = ItemMaster.query.filter_by(item_code=code, item_type_id=rm_type.id).first()
                if not item:
                    missing_items.append(code)
            
            if missing_items:
                print(f"\nFound {len(missing_items)} items in RawMaterialStocktake that are not marked as RM in ItemMaster:")
                for code in missing_items[:10]:  # Show first 10 missing items
                    item = ItemMaster.query.filter_by(item_code=code).first()
                    if item:
                        print(f"  - {code}: Currently marked as type {item.item_type.type_name}")
                    else:
                        print(f"  - {code}: Not found in ItemMaster")
                
                if len(missing_items) > 10:
                    print(f"  ... and {len(missing_items) - 10} more")
            
        except Exception as e:
            print(f"Error checking raw materials: {str(e)}")

if __name__ == '__main__':
    check_raw_materials() 