from app import app, db
from models.item_master import ItemMaster
import logging

logger = logging.getLogger(__name__)

def verify_calculation_factors():
    """
    Verifies and fixes calculation factors in item_master table.
    """
    with app.app_context():
        try:
            # Get all WIP items
            wip_items = ItemMaster.query.join(ItemMaster.item_type).filter(
                ItemMaster.item_type.has(type_name='WIP')
            ).all()
            
            logger.info(f"Found {len(wip_items)} WIP items")
            
            # Check and fix calculation factors
            for item in wip_items:
                print(f"\nItem: {item.item_code}")
                print(f"  Description: {item.description}")
                # print(f"  Current Calculation Factor: {item.calculation_factor}")  # REMOVED - calculation_factor no longer exists
                print(f"  Current kg_per_unit: {item.kg_per_unit}")
                print(f"  Current units_per_bag: {item.units_per_bag}")
                print(f"  Current avg_weight_per_unit: {item.avg_weight_per_unit}")
                
                # If calculation_factor is None or 0, try to calculate it
                # if not item.calculation_factor or float(item.calculation_factor) == 0:  # REMOVED - calculation_factor no longer exists
                #     # Try to calculate from other fields
                #     if item.kg_per_unit and float(item.kg_per_unit) > 0:
                #         item.calculation_factor = float(item.kg_per_unit)  # REMOVED - calculation_factor no longer exists
                #         print(f"  Setting calculation_factor to kg_per_unit: {item.calculation_factor}")  # REMOVED - calculation_factor no longer exists
                #     elif item.avg_weight_per_unit and float(item.avg_weight_per_unit) > 0:
                #         item.calculation_factor = float(item.avg_weight_per_unit)  # REMOVED - calculation_factor no longer exists
                #         print(f"  Setting calculation_factor to avg_weight_per_unit: {item.calculation_factor}")  # REMOVED - calculation_factor no longer exists
                #     else:
                #         # Default to 1.0 if no other value available
                #         item.calculation_factor = 1.0  # REMOVED - calculation_factor no longer exists
                #         print("  Setting default calculation_factor: 1.0")  # REMOVED - calculation_factor no longer exists
            
            # Commit changes
            db.session.commit()
            logger.info("Successfully verified and fixed calculation factors")
            
            # Print final summary
            print("\nFinal Calculation Factors:")
            print("-" * 80)
            for item in wip_items:
                print(f"Item: {item.item_code}")
                print(f"  Description: {item.description}")
                # print(f"  Calculation Factor: {item.calculation_factor}")  # REMOVED - calculation_factor no longer exists
                print("-" * 40)
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error verifying calculation factors: {str(e)}")
            raise

if __name__ == '__main__':
    verify_calculation_factors() 