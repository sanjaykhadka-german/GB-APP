from app import app, db
from models.packing import Packing
from models.filling import Filling
from models.production import Production
from models.item_master import ItemMaster
import logging
from datetime import datetime
import math

logger = logging.getLogger(__name__)

def calculate_batches(total_kg):
    """Calculate number of batches based on total kg (300kg per batch)"""
    return math.ceil(total_kg / 300) if total_kg > 0 else 0

def sync_packing_to_filling_production():
    """
    Directly sync packing entries to filling and production tables based on relationships.
    No complex BOM calculations, just direct 1:1 relationships.
    """
    with app.app_context():
        try:
            # Get all packing entries
            packing_entries = Packing.query.all()
            logger.info(f"Found {len(packing_entries)} packing entries")
            
            # Clear existing filling and production entries
            Filling.query.delete()
            Production.query.delete()
            db.session.commit()
            logger.info("Cleared existing filling and production entries")
            
            # Process each packing entry
            for packing in packing_entries:
                fg_item = packing.item
                if not fg_item:
                    logger.warning(f"Packing entry {packing.id} has no associated item")
                    continue
                    
                logger.info(f"Processing packing entry for {fg_item.item_code}")
                
                # Get WIP and WIPF components
                wip_component = fg_item.wip_item
                wipf_component = fg_item.wipf_item
                
                # Create production entry if WIP exists
                if wip_component:
                    # Generate production code
                    prod_code = f"PROD-{wip_component.item_code}-{packing.packing_date.strftime('%Y%m%d')}"
                    
                    # Calculate batches based on total_kg
                    total_kg = packing.requirement_kg
                    batches = calculate_batches(total_kg)
                    
                    prod = Production(
                        production_date=packing.packing_date,
                        week_commencing=packing.week_commencing,
                        item_id=wip_component.id,
                        total_kg=total_kg,
                        requirement_kg=total_kg,
                        machinery_id=packing.machinery_id,
                        department_id=packing.department_id,
                        production_code=prod_code,  # Set required production code
                        description=wip_component.description,  # Set description from WIP item
                        batches=batches,  # Calculate batches based on total_kg
                        priority=1  # Default priority
                    )
                    db.session.add(prod)
                    logger.info(f"Created production entry for WIP {wip_component.item_code}: {total_kg}kg ({batches} batches)")
                
                # Create filling entry if WIPF exists
                if wipf_component:
                    fill = Filling(
                        filling_date=packing.packing_date,
                        week_commencing=packing.week_commencing,
                        item_id=wipf_component.id,
                        requirement_kg=packing.requirement_kg,
                        kilo_per_size=packing.requirement_kg,
                        machinery_id=packing.machinery_id,
                        department_id=packing.department_id
                    )
                    db.session.add(fill)
                    logger.info(f"Created filling entry for WIPF {wipf_component.item_code}: {packing.requirement_kg}kg")
            
            db.session.commit()
            logger.info("Successfully synced all entries")
            
            # Print summary
            print("\nSummary:")
            print("-" * 80)
            print(f"Total packing entries processed: {len(packing_entries)}")
            print(f"Production entries created: {Production.query.count()}")
            print(f"Filling entries created: {Filling.query.count()}")
            
            # Print batch details
            print("\nProduction Batch Details:")
            print("-" * 80)
            for prod in Production.query.all():
                print(f"WIP: {prod.item.item_code}, Total KG: {prod.total_kg}, Batches: {prod.batches}")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error syncing entries: {str(e)}")
            raise

if __name__ == '__main__':
    sync_packing_to_filling_production() 