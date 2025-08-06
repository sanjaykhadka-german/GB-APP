from app import app
from models.production import Production
from database import db
import json

def test_production_autocomplete():
    with app.app_context():
        print("Testing Production Autocomplete")
        print("=" * 40)
        
        # Check if there's any production data
        production_count = Production.query.count()
        print(f"Total production records: {production_count}")
        
        if production_count > 0:
            # Show sample records
            sample_productions = Production.query.limit(5).all()
            print("\nSample production records:")
            for prod in sample_productions:
                print(f"  ID: {prod.id}")
                print(f"  Production Code: {prod.production_code}")
                print(f"  Description: {prod.description}")
                print(f"  Date: {prod.production_date}")
                print("  ---")
            
            # Test the autocomplete logic directly
            print("\nTesting autocomplete logic:")
            test_queries = ['1', '10', 'WIP', 'Test']
            
            for query in test_queries:
                print(f"\nSearching for '{query}':")
                results = Production.query.filter(
                    Production.production_code.ilike(f"%{query}%")
                ).limit(10).all()
                
                suggestions = [
                    {
                        "production_code": production.production_code,
                        "description": production.description
                    }
                    for production in results
                    if production.production_code and production.description
                ]
                
                print(f"  Found {len(suggestions)} matches:")
                for suggestion in suggestions[:3]:  # Show first 3
                    print(f"    {suggestion['production_code']} - {suggestion['description']}")
                    
        else:
            print("❌ No production data found! This is why autocomplete isn't working.")
            print("\nCreate some test production data first.")

if __name__ == '__main__':
    test_production_autocomplete() 