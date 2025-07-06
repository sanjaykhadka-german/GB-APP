from app import app
from controllers.bom_service import update_downstream_requirements
from datetime import datetime, date
from models.packing import Packing
from models.filling import Filling
from models.production import Production
from models.item_master import ItemMaster
from database import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_bom_service():
    with app.app_context():
        try:
            # Use the actual dates that have packing entries
            packing_date = date(2025, 7, 4)  # July 4th, 2025
            week_commencing = date(2025, 7, 7)  # July 7th, 2025
            
            # Get all packing entries
            packing_entries = Packing.query.filter_by(
                packing_date=packing_date,
                week_commencing=week_commencing
            ).all()
            
            logger.info(f"Found {len(packing_entries)} packing entries for {packing_date} (week {week_commencing})")
            
            # Print details of each packing entry
            for packing in packing_entries:
                fg_item = packing.item
                if not fg_item:
                    logger.warning(f"Packing entry {packing.id} has no associated item")
                    continue
                    
                logger.info(f"\nPacking Entry:")
                logger.info(f"  FG Item: {fg_item.item_code} ({fg_item.description})")
                logger.info(f"  Requirement KG: {packing.requirement_kg}")
                
                # Check WIP and WIPF components
                wip = fg_item.wip_component
                wipf = fg_item.wipf_component
                
                logger.info(f"  WIP Component: {wip.item_code if wip else 'None'}")
                logger.info(f"  WIPF Component: {wipf.item_code if wipf else 'None'}")
            
            # Try to update downstream requirements
            logger.info("\nUpdating downstream requirements...")
            success, message = update_downstream_requirements(packing_date, week_commencing)
            
            if success:
                logger.info("Successfully updated downstream requirements")
                
                # Check created entries
                filling_entries = Filling.query.filter_by(
                    filling_date=packing_date,
                    week_commencing=week_commencing
                ).all()
                production_entries = Production.query.filter_by(
                    production_date=packing_date,
                    week_commencing=week_commencing
                ).all()
                
                logger.info(f"\nCreated {len(filling_entries)} filling entries:")
                for filling in filling_entries:
                    logger.info(f"  WIPF: {filling.item.item_code}, KG: {filling.requirement_kg}")
                    
                logger.info(f"\nCreated {len(production_entries)} production entries:")
                for production in production_entries:
                    logger.info(f"  WIP: {production.item.item_code}, KG: {production.total_kg}")
            else:
                logger.error(f"Failed to update downstream requirements: {message}")
                
        except Exception as e:
            logger.error(f"Error testing BOM service: {str(e)}")
            raise

if __name__ == '__main__':
    test_bom_service() 