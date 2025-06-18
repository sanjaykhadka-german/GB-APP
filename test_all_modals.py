#!/usr/bin/env python3
"""
Test script to verify all modal functionality for category, department, UOM, and machinery
"""

import requests
import json

# Test the API endpoints for all entities
BASE_URL = "http://localhost:5000"

def test_all_endpoints():
    print("Testing All Modal Functionality...")
    print("=" * 60)
    
    # Test 1: Get existing item types
    print("1. Testing GET /item-type (list item types)")
    try:
        response = requests.get(f"{BASE_URL}/item-type")
        if response.status_code == 200:
            item_types = response.json()
            print(f"   ✓ Found {len(item_types)} existing item types")
        else:
            print(f"   ✗ Failed to get item types: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print()
    
    # Test 2: Get existing categories
    print("2. Testing GET /category (list categories)")
    try:
        response = requests.get(f"{BASE_URL}/category")
        if response.status_code == 200:
            categories = response.json()
            print(f"   ✓ Found {len(categories)} existing categories")
        else:
            print(f"   ✗ Failed to get categories: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print()
    
    # Test 3: Get existing departments
    print("3. Testing GET /department (list departments)")
    try:
        response = requests.get(f"{BASE_URL}/department")
        if response.status_code == 200:
            departments = response.json()
            print(f"   ✓ Found {len(departments)} existing departments")
        else:
            print(f"   ✗ Failed to get departments: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print()
    
    # Test 4: Get existing UOMs
    print("4. Testing GET /uom (list UOMs)")
    try:
        response = requests.get(f"{BASE_URL}/uom")
        if response.status_code == 200:
            uoms = response.json()
            print(f"   ✓ Found {len(uoms)} existing UOMs")
        else:
            print(f"   ✗ Failed to get UOMs: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print()
    
    # Test 5: Get existing machinery
    print("5. Testing GET /machinery (list machinery)")
    try:
        response = requests.get(f"{BASE_URL}/machinery")
        if response.status_code == 200:
            machinery = response.json()
            print(f"   ✓ Found {len(machinery)} existing machinery")
        else:
            print(f"   ✗ Failed to get machinery: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print()
    print("=" * 60)
    print("API Endpoint Tests Completed!")
    print("\nTo test the modal functionality:")
    print("1. Start the Flask app: python app.py")
    print("2. Navigate to: http://localhost:5000/item-master/create")
    print("3. Test each dropdown by clicking the '+' button:")
    print("   - Item Type: Click '+' next to Item Type dropdown")
    print("   - Category: Click '+' next to Category dropdown")
    print("   - Department: Click '+' next to Department dropdown")
    print("   - UOM: Click '+' next to UOM dropdown")
    print("   - Machinery: Click '+' next to Machinery dropdown")
    print("4. Enter a new name in each modal and click 'Save'")
    print("5. Verify the new items appear in their respective dropdowns")

def test_create_endpoints():
    print("\nTesting Create Endpoints...")
    print("=" * 60)
    
    test_data = [
        ("item-type", {"type_name": "test_item_type_modal"}),
        ("category", {"name": "test_category_modal"}),
        ("department", {"departmentName": "test_department_modal"}),
        ("uom", {"UOMName": "test_uom_modal"}),
        ("machinery", {"machineryName": "test_machinery_modal"})
    ]
    
    for endpoint, data in test_data:
        print(f"Testing POST /{endpoint}")
        try:
            response = requests.post(
                f"{BASE_URL}/{endpoint}",
                headers={"Content-Type": "application/json"},
                data=json.dumps(data)
            )
            if response.status_code == 200:
                result = response.json()
                print(f"   ✓ Successfully created {endpoint}: {result}")
            else:
                print(f"   ✗ Failed to create {endpoint}: {response.status_code}")
                print(f"     Response: {response.text}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        print()

if __name__ == "__main__":
    test_all_endpoints()
    test_create_endpoints() 