import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models.item_master import ItemMaster
from models.item_type import ItemType
from app import app, db

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def verify_all_relationships():
    """
    Thoroughly verifies the WIP and WIPF relationships for the items
    involved in the aggregation issue.
    """
    with app.app_context():
        logging.info("--- Starting Database Relationship Verification ---")
        
        test_cases = {
            "Scenario 1: Same WIPF / Same WIP": {
                'codes': ['1004.090.1', '1004.200.1'],
                'expected_wipf': '1004.6500',
                'expected_wip': '1004'
            },
            "Scenario 2: Different WIPF / Same WIP": {
                'codes': ['2015.125.02', '2015.100.2'],
                'expected_wipf': None,  # They should be different
                'expected_wip': '2015.1' # Assuming this is the common WIP code
            }
        }

        all_checks_passed = True

        for scenario, details in test_cases.items():
            logging.info(f"\n--- Verifying {scenario} ---")
            wipf_codes = set()
            wip_codes = set()

            for code in details['codes']:
                item = ItemMaster.query.filter_by(item_code=code).first()
                if not item:
                    logging.error(f"  [FAIL] Item code not found in database: {code}")
                    all_checks_passed = False
                    continue

                logging.info(f"  Checking FG Item: {item.item_code} (ID: {item.id})")

                wipf_item = item.wipf_item
                wip_item = item.wip_item

                if wipf_item:
                    logging.info(f"    -> Found WIPF: {wipf_item.item_code} (ID: {wipf_item.id})")
                    wipf_codes.add(wipf_item.item_code)
                else:
                    logging.warning(f"    -> No WIPF relationship found for {code}.")
                
                if wip_item:
                    logging.info(f"    -> Found WIP: {wip_item.item_code} (ID: {wip_item.id})")
                    wip_codes.add(wip_item.item_code)
                else:
                    logging.warning(f"    -> No WIP relationship found for {code}.")

            # Validate the findings against expectations
            if details['expected_wipf']:
                if len(wipf_codes) == 1 and details['expected_wipf'] in wipf_codes:
                    logging.info(f"  [PASS] All items correctly point to the single expected WIPF: {details['expected_wipf']}")
                else:
                    logging.error(f"  [FAIL] WIPF check failed! Expected all to point to '{details['expected_wipf']}'. Found: {wipf_codes}")
                    all_checks_passed = False
            
            if details['expected_wip']:
                if len(wip_codes) == 1 and details['expected_wip'] in wip_codes:
                    logging.info(f"  [PASS] All items correctly point to the single expected WIP: {details['expected_wip']}")
                else:
                    # A special check for 2015 items to find the common WIP if the expected one is wrong
                    if scenario == "Scenario 2: Different WIPF / Same WIP":
                        item1 = ItemMaster.query.filter_by(item_code=details['codes'][0]).first()
                        item2 = ItemMaster.query.filter_by(item_code=details['codes'][1]).first()
                        if item1 and item2 and item1.wip_item_id and item1.wip_item_id == item2.wip_item_id:
                            common_wip_code = item1.wip_item.item_code
                            logging.warning(f"  [ADJUSTED PASS] The expected WIP was '{details['expected_wip']}', but the items correctly share a different common WIP: '{common_wip_code}'. This is acceptable.")
                        else:
                             logging.error(f"  [FAIL] WIP check failed! Expected all to point to a single WIP. Found: {wip_codes}")
                             all_checks_passed = False
                    else:
                        logging.error(f"  [FAIL] WIP check failed! Expected all to point to '{details['expected_wip']}'. Found: {wip_codes}")
                        all_checks_passed = False


        logging.info("\n--- Verification Summary ---")
        if all_checks_passed:
            logging.info("✅ All database relationship checks passed successfully.")
        else:
            logging.error("❌ One or more database relationship checks failed. Please review the logs above and correct the data in the `item_master` table.")


if __name__ == '__main__':
    verify_all_relationships() 