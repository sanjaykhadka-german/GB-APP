#!/usr/bin/env python3
"""
Test script to verify item type modal functionality
"""

import requests
import json

# Test the item type API endpoints
BASE_URL = "http://localhost:5000"

def test_item_type_endpoints():
    print("Testing Item Type Modal Functionality...")
    print("=" * 50)
    
    # Test 1: Get existing item types
    print("1. Testing GET /item-type (list item types)")
    try:
        response = requests.get(f"{BASE_URL}/item-type")
        if response.status_code == 200:
            item_types = response.json()
            print(f"   ✓ Found {len(item_types)} existing item types")
            for item_type in item_types:
                print(f"     - {item_type['type_name']} (ID: {item_type['id']})")
        else:
            print(f"   ✗ Failed to get item types: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print()
    
    # Test 2: Create a new item type
    print("2. Testing POST /item-type (create new item type)")
    test_type_name = "test_item_type_modal"
    try:
        data = {"type_name": test_type_name}
        response = requests.post(
            f"{BASE_URL}/item-type",
            headers={"Content-Type": "application/json"},
            data=json.dumps(data)
        )
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ Successfully created item type: {test_type_name}")
            print(f"     Response: {result}")
        else:
            print(f"   ✗ Failed to create item type: {response.status_code}")
            print(f"     Response: {response.text}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print()
    print("=" * 50)
    print("Test completed!")
    print("\nTo test the modal functionality:")
    print("1. Start the Flask app: python app.py")
    print("2. Navigate to: http://localhost:5000/item-master/create")
    print("3. Click the '+' button next to the Item Type dropdown")
    print("4. Enter a new item type name and click 'Save Item Type'")
    print("5. Verify the new item type appears in the dropdown")

if __name__ == "__main__":
    test_item_type_endpoints() 