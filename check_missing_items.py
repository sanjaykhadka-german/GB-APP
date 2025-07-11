from app import app
from database import db
from models.raw_material_stocktake import RawMaterialStocktake
from models.item_master import ItemMaster
from models.item_type import ItemType

def check_missing_items():
    with app.app_context():
        try:
            print("Checking for missing items...")
            
            # Get RM type ID
            rm_type = ItemType.query.filter_by(type_name='RM').first()
            if not rm_type:
                print("Error: RM item type not found")
                return
                
            # Get all item codes from RawMaterialStocktake
            stocktake_items = db.session.query(RawMaterialStocktake.item_code).distinct().all()
            if not stocktake_items:
                print("No items found in RawMaterialStocktake")
                return
                
            stocktake_codes = [item[0] for item in stocktake_items]
            print(f"\nFound {len(stocktake_codes)} unique item codes in RawMaterialStocktake")
            
            # Get all item codes from ItemMaster that are raw materials
            item_master_codes = db.session.query(ItemMaster.item_code).filter(
                ItemMaster.item_type_id == rm_type.id
            ).all()
            if not item_master_codes:
                print("No raw material items found in ItemMaster")
                return
                
            item_master_codes = [item[0] for item in item_master_codes]
            print(f"Found {len(item_master_codes)} raw material items in ItemMaster")
            
            # Find missing items
            missing_codes = set(stocktake_codes) - set(item_master_codes)
            print(f"\nMissing items ({len(missing_codes)}):")
            for code in sorted(missing_codes):
                # Get sample stocktake record for this item
                stocktake = RawMaterialStocktake.query.filter_by(item_code=code).first()
                if stocktake:
                    print(f"Item Code: {code}")
                    print(f"Current Stock: {stocktake.current_stock}")
                    print(f"Price UOM: {stocktake.price_uom}")
                    print(f"Stock Value: {stocktake.stock_value}")
                    print("---")
            
        except Exception as e:
            print(f"Error checking missing items: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    check_missing_items() 