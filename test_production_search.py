from app import app
from models.production import Production
from datetime import datetime, date, timedelta
import requests
import json

def test_production_search():
    with app.app_context():
        print("=== Testing Production Search ===")
        
        # 1. Check total production records
        total_count = Production.query.count()
        print(f"Total production records: {total_count}")
        
        if total_count == 0:
            print("❌ No production records found! This is why search doesn't work.")
            return
        
        # 2. Show sample records
        sample_productions = Production.query.limit(5).all()
        print(f"\nSample production records:")
        for prod in sample_productions:
            print(f"  ID: {prod.id}")
            print(f"  Week: {prod.week_commencing}")
            print(f"  Date: {prod.production_date}")
            print(f"  Code: {prod.production_code}")
            print(f"  Description: {prod.description}")
            print(f"  Total KG: {prod.total_kg}")
            print("  ---")
        
        # 3. Test current week filter
        today = date.today()
        current_week = today - timedelta(days=today.weekday())
        print(f"\nTesting current week filter: {current_week}")
        
        current_week_productions = Production.query.filter_by(week_commencing=current_week).all()
        print(f"Productions for current week: {len(current_week_productions)}")
        
        # 4. Test different weeks
        print(f"\nAll unique weeks in production data:")
        weeks = Production.query.with_entities(Production.week_commencing).distinct().all()
        for week in weeks:
            if week[0]:
                week_count = Production.query.filter_by(week_commencing=week[0]).count()
                print(f"  Week {week[0]}: {week_count} records")
        
        # 5. Test search endpoint directly (if app is running)
        try:
            print(f"\n=== Testing AJAX Search Endpoint ===")
            
            # Test empty search
            response = requests.get('http://localhost:5000/get_search_productions', timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"Empty search returned: {len(data.get('productions', []))} records")
            
            # Test week search
            if weeks:
                test_week = weeks[0][0].strftime('%Y-%m-%d')
                response = requests.get(f'http://localhost:5000/get_search_productions?week_commencing={test_week}', timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    print(f"Week {test_week} search returned: {len(data.get('productions', []))} records")
                    
        except Exception as e:
            print(f"Could not test AJAX endpoint: {e}")
            print("Make sure the Flask app is running on localhost:5000")

if __name__ == '__main__':
    test_production_search() 