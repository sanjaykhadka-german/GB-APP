from app import app, db
from models.soh import SOH
from models.item_master import ItemMaster

def check_records():
    try:
        with app.app_context():
            # Check SOH records
            total_soh = SOH.query.count()
            print(f'Total SOH records: {total_soh}')
            
            if total_soh > 0:
                print('\nSample SOH records:')
                sample_soh = SOH.query.limit(5).all()
                for record in sample_soh:
                    print(f'SOH - ID: {record.id}, FG Code: {record.fg_code}, Item ID: {record.item_id}, Week Commencing: {record.week_commencing}')
            
            # Check ItemMaster records
            total_items = ItemMaster.query.count()
            print(f'\nTotal ItemMaster records: {total_items}')
            
            if total_items > 0:
                print('\nSample ItemMaster records:')
                sample_items = ItemMaster.query.limit(5).all()
                for item in sample_items:
                    print(f'Item - ID: {item.id}, Item Code: {item.item_code}')
            
            # Check for any SOH records with missing item_id
            missing_items = SOH.query.filter(SOH.item_id.is_(None)).count()
            print(f'\nSOH records with missing item_id: {missing_items}')
    except Exception as e:
        print(f'Error: {str(e)}')
        # Print more details about the error
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_records() 