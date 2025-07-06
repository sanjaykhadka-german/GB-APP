from app import app
from models.packing import Packing
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_packing_dates():
    with app.app_context():
        try:
            # Get all unique packing dates
            dates = Packing.query.with_entities(
                Packing.packing_date,
                Packing.week_commencing
            ).distinct().all()
            
            logger.info(f"Found {len(dates)} unique date pairs")
            
            for packing_date, week_commencing in dates:
                # Count entries for this date pair
                count = Packing.query.filter_by(
                    packing_date=packing_date,
                    week_commencing=week_commencing
                ).count()
                
                logger.info(f"Date: {packing_date}, Week: {week_commencing}, Entries: {count}")
                
        except Exception as e:
            logger.error(f"Error checking packing dates: {str(e)}")
            raise

if __name__ == '__main__':
    check_packing_dates() 