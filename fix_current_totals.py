from app import create_app
from controllers.packing_controller import re_aggregate_filling_and_production_for_date
from datetime import datetime

app = create_app()

with app.app_context():
    # Fix your specific date
    packing_date = datetime.strptime('2025-06-30', '%Y-%m-%d').date()
    week_commencing = datetime.strptime('2025-06-30', '%Y-%m-%d').date()
    
    print(f"Re-aggregating for date: {packing_date}, week: {week_commencing}")
    re_aggregate_filling_and_production_for_date(packing_date, week_commencing)
    print("Re-aggregation completed!") 