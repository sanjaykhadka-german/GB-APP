from app import db
from models.soh import SOH
from models.packing import Packing
from datetime import timedelta

def get_monday_of_week(dt):
    return dt - timedelta(days=dt.weekday())

for packing in Packing.query.all():
    week_commencing = get_monday_of_week(packing.packing_date)
    soh = SOH.query.filter_by(fg_code=packing.product_code, week_commencing=week_commencing).first()
    if not soh:
        print(f"No SOH entry for Packing ID {packing.id}, product_code {packing.product_code}, week_commencing {week_commencing}")
        # Optionally, update or delete the Packing entry
        packing.week_commencing = week_commencing
        db.session.commit()
    else:
        packing.week_commencing = week_commencing
        db.session.commit()