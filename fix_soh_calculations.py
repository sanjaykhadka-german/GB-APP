from app import app, db
from models.production import Production
from models.item_master import ItemMaster
import logging

logger = logging.getLogger(__name__)

def update_soh_calculations():
    """
    Updates SOH calculations for all production entries using calculation_factor from item_master.
    """
    with app.app_context():
        try:
            # Get all production entries
            production_entries = Production.query.all()
            logger.info(f"Found {len(production_entries)} production entries")
            
            for prod in production_entries:
                # Get the item and its calculation factor
                item = prod.item
                if not item:
                    logger.warning(f"Production entry {prod.id} has no associated item")
                    continue
                
                calculation_factor = float(item.calculation_factor or 1.0)
                total_kg = float(prod.total_kg or 0.0)
                
                # Calculate total stock units using calculation factor
                total_stock_units = total_kg / calculation_factor if calculation_factor > 0 else 0
                
                # Update the production entry
                prod.total_kg = total_kg
                prod.batches = total_kg / 300 if total_kg > 0 else 0  # 300kg per batch
                
                # Log the update
                logger.info(f"Updated production {prod.id}:")
                logger.info(f"  Item: {item.item_code}")
                logger.info(f"  Calculation Factor: {calculation_factor}")
                logger.info(f"  Total KG: {total_kg}")
                logger.info(f"  Total Stock Units: {total_stock_units}")
                logger.info(f"  Batches: {prod.batches}")
            
            # Commit all changes
            db.session.commit()
            logger.info("Successfully updated all SOH calculations")
            
            # Print summary
            print("\nSummary of Updates:")
            print("-" * 80)
            for prod in Production.query.all():
                item = prod.item
                if item:
                    print(f"Item: {item.item_code}")
                    print(f"  Total KG: {prod.total_kg}")
                    print(f"  Calculation Factor: {item.calculation_factor}")
                    print(f"  Total Stock Units: {prod.total_kg / float(item.calculation_factor) if item.calculation_factor else 0}")
                    print(f"  Batches: {prod.batches}")
                    print("-" * 40)
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating SOH calculations: {str(e)}")
            raise

if __name__ == '__main__':
    update_soh_calculations() 