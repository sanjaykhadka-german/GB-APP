from app import app, db
from models.item_master import ItemMaster
from models.packing import Packing
from models.filling import Filling
from models.production import Production

def check_relationships():
    with app.app_context():
        # Check 1004.090.1 and 1004.200 relationships
        print("\nChecking 1004.090.1 and 1004.200 relationships:")
        codes_1004 = ['1004.090.1', '1004.200']
        for code in codes_1004:
            item = ItemMaster.query.filter_by(item_code=code).first()
            if item:
                print(f"\nFG: {item.item_code}")
                if item.wipf_item:
                    print(f"  WIPF: {item.wipf_item.item_code}")
                if item.wip_item:
                    print(f"  WIP: {item.wip_item.item_code}")
            else:
                print(f"Item not found: {code}")

        # Check 2015.125.02 and 2015.100.2 relationships
        print("\nChecking 2015.125.02 and 2015.100.2 relationships:")
        codes_2015 = ['2015.125.02', '2015.100.2']
        for code in codes_2015:
            item = ItemMaster.query.filter_by(item_code=code).first()
            if item:
                print(f"\nFG: {item.item_code}")
                if item.wipf_item:
                    print(f"  WIPF: {item.wipf_item.item_code}")
                if item.wip_item:
                    print(f"  WIP: {item.wip_item.item_code}")
            else:
                print(f"Item not found: {code}")

        # Check actual aggregation in database
        print("\nChecking actual aggregation in database:")
        week_commencing = Packing.query.first().week_commencing  # Get a sample week
        
        print(f"\nPacking entries for week {week_commencing}:")
        packing_entries = Packing.query.filter_by(week_commencing=week_commencing).all()
        for packing in packing_entries:
            print(f"Packing: {packing.item.item_code} - {packing.requirement_kg} kg")
            
        print(f"\nFilling entries for week {week_commencing}:")
        filling_entries = Filling.query.filter_by(week_commencing=week_commencing).all()
        for filling in filling_entries:
            print(f"Filling: {filling.item.item_code} - {filling.requirement_kg} kg")
            
        print(f"\nProduction entries for week {week_commencing}:")
        production_entries = Production.query.filter_by(week_commencing=week_commencing).all()
        for production in production_entries:
            print(f"Production: {production.item.item_code} - {production.total_kg} kg")

if __name__ == '__main__':
    check_relationships() 