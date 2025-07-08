import logging
from datetime import date
from app import app, db
from models.item_master import ItemMaster
from models.packing import Packing
from models.filling import Filling
from models.production import Production
from models.soh import SOH
from models.machinery import Machinery
from controllers.bom_service import BOMService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_aggregation_test():
    """
    A dedicated test to validate the downstream aggregation logic of the BOMService.
    This test operates within a single transaction and rolls back at the end
    to ensure the database is not permanently altered.
    """
    with app.app_context():
        logging.info("--- Starting Aggregation Logic Test ---")
        
        # Define test parameters
        test_week = date(2025, 7, 14)
        product_codes = {
            '1004.090.1': 25000,
            '1004.200.1': 25000,
            '2015.125.02': 20500,
            '2015.100.2': 21900
        }
        
        # --- Transaction Start ---
        try:
            # Ensure a clean slate for the test week
            logging.info(f"Clearing any existing test data for week {test_week}...")
            Packing.query.filter_by(week_commencing=test_week).delete()
            Filling.query.filter_by(week_commencing=test_week).delete()
            Production.query.filter_by(week_commencing=test_week).delete()
            SOH.query.filter_by(week_commencing=test_week).delete()
            
            # Get or create a dummy machinery record
            machinery = Machinery.query.first()
            if not machinery:
                machinery = Machinery(machineryName='Test Machine')
                db.session.add(machinery)

            # Create the necessary Packing and SOH entries
            logging.info("Creating prerequisite Packing and SOH entries...")
            for code, kg in product_codes.items():
                item = ItemMaster.query.filter_by(item_code=code).first()
                if not item:
                    logging.error(f"Test setup failed: Item code {code} not found.")
                    raise Exception(f"ItemNotFound: {code}")

                # Create SOH entry
                soh = SOH(item_id=item.id, week_commencing=test_week, soh_total_units=0)
                db.session.add(soh)

                # Create Packing entry
                packing = Packing(
                    item_id=item.id,
                    week_commencing=test_week,
                    packing_date=test_week, # Use week_commencing as packing_date for simplicity
                    requirement_kg=kg,
                    machinery_id=machinery.machineID
                )
                db.session.add(packing)
            
            db.session.flush() # Flush to assign IDs
            logging.info("Test data created successfully.")

            # --- Invoke the service ---
            logging.info("Calling BOMService.update_downstream_requirements...")
            success = BOMService.update_downstream_requirements(week_commencing=test_week)
            if not success:
                raise Exception("BOMService call failed.")
            logging.info("BOMService call completed.")

            # --- Verification ---
            logging.info("--- Verifying Results ---")
            all_tests_passed = True

            # Scenario 1 Verification
            wipf_1004 = ItemMaster.query.filter_by(item_code='1004.6500').first()
            filling_1004 = Filling.query.filter_by(item_id=wipf_1004.id, week_commencing=test_week).all()
            if len(filling_1004) == 1 and filling_1004[0].requirement_kg == 50000:
                logging.info("[PASS] Scenario 1 (Filling): Correctly created 1 filling entry for 1004.6500 with 50,000 kg.")
            else:
                logging.error(f"[FAIL] Scenario 1 (Filling): Expected 1 entry for 50,000 kg. Found {len(filling_1004)} entries with kgs: {[f.requirement_kg for f in filling_1004]}")
                all_tests_passed = False

            wip_1004 = ItemMaster.query.filter_by(item_code='1004').first()
            prod_1004 = Production.query.filter_by(item_id=wip_1004.id, week_commencing=test_week).all()
            if len(prod_1004) == 1 and prod_1004[0].total_kg == 50000:
                logging.info("[PASS] Scenario 1 (Production): Correctly created 1 production entry for 1004 with 50,000 kg.")
            else:
                logging.error(f"[FAIL] Scenario 1 (Production): Expected 1 entry for 50,000 kg. Found {len(prod_1004)} entries with kgs: {[p.total_kg for p in prod_1004]}")
                all_tests_passed = False

            # Scenario 2 Verification
            wipf_2015_125 = ItemMaster.query.filter_by(item_code='2015.125').first()
            wipf_2015_100 = ItemMaster.query.filter_by(item_code='2015.100').first()
            filling_2015_125 = Filling.query.filter_by(item_id=wipf_2015_125.id, week_commencing=test_week).first()
            filling_2015_100 = Filling.query.filter_by(item_id=wipf_2015_100.id, week_commencing=test_week).first()

            if filling_2015_125 and filling_2015_100 and filling_2015_125.requirement_kg == 20500 and filling_2015_100.requirement_kg == 21900:
                 logging.info("[PASS] Scenario 2 (Filling): Correctly created 2 separate filling entries with correct kgs.")
            else:
                logging.error(f"[FAIL] Scenario 2 (Filling): Check failed. 2015.125 kg: {filling_2015_125.requirement_kg if filling_2015_125 else 'Not found'}. 2015.100 kg: {filling_2015_100.requirement_kg if filling_2015_100 else 'Not found'}")
                all_tests_passed = False

            wip_2015 = ItemMaster.query.filter_by(item_code='2015').first()
            prod_2015 = Production.query.filter_by(item_id=wip_2015.id, week_commencing=test_week).all()
            if len(prod_2015) == 1 and prod_2015[0].total_kg == 42400:
                logging.info("[PASS] Scenario 2 (Production): Correctly created 1 production entry for 2015 with 42,400 kg.")
            else:
                logging.error(f"[FAIL] Scenario 2 (Production): Expected 1 entry for 42,400 kg. Found {len(prod_2015)} entries with kgs: {[p.total_kg for p in prod_2015]}")
                all_tests_passed = False
            
            if all_tests_passed:
                logging.info("\n✅✅✅ All aggregation logic tests passed! ✅✅✅")
            else:
                logging.error("\n❌❌❌ One or more aggregation logic tests failed. ❌❌❌")


        except Exception as e:
            logging.error(f"An error occurred during the test: {e}", exc_info=True)
        
        finally:
            # --- Transaction Rollback ---
            logging.warning("Rolling back transaction. No changes were saved to the database.")
            db.session.rollback()


if __name__ == '__main__':
    run_aggregation_test() 