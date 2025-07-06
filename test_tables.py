from app import app, db
from models.filling import Filling
from models.production import Production
from models.item_master import ItemMaster
from datetime import date

def test_create_entries():
    with app.app_context():
        try:
            # Get a test item from item_master
            test_item = ItemMaster.query.first()
            
            if not test_item:
                print("No test item found in item_master")
                return
                
            print(f"\nUsing test item: {test_item.item_code} - {test_item.description}")
                
            # Try creating a filling entry
            filling = Filling(
                filling_date=date.today(),
                week_commencing=date.today(),
                item_id=test_item.id,
                kilo_per_size=1.0,
                requirement_kg=100.0
            )
            
            db.session.add(filling)
            print("\nAdded filling entry")
            
            # Try creating a production entry
            production = Production(
                production_date=date.today(),
                week_commencing=date.today(),
                item_id=test_item.id,
                production_code=test_item.item_code,  # Use item code as production code
                description=test_item.description,    # Use item description
                total_kg=100.0,
                requirement_kg=100.0,
                priority=1
            )
            
            db.session.add(production)
            print("Added production entry")
            
            # Commit the changes
            db.session.commit()
            print("Successfully committed changes")
            
            # Verify the entries were created
            filling_count = Filling.query.count()
            production_count = Production.query.count()
            
            print(f"\nCurrent table counts:")
            print(f"Filling entries: {filling_count}")
            print(f"Production entries: {production_count}")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    test_create_entries() 