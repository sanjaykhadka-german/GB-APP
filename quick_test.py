#!/usr/bin/env python3
"""
Quick Test Script for GB-APP
Verifies application status and basic functionality
"""

import requests
import json
import os
import re
from datetime import datetime

def test_application_status():
    """Test if the application is running and accessible"""
    print("🔍 Testing Application Status")
    print("=" * 40)
    
    try:
        # Test basic connectivity
        response = requests.get("http://localhost:5000/", timeout=5)
        if response.status_code == 200:
            print("✅ Application is running and accessible")
            return True
        else:
            print(f"⚠️ Application responded with status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Application is not running")
        return False
    except Exception as e:
        print(f"❌ Error connecting to application: {e}")
        return False

def test_critical_endpoints():
    """Test critical endpoints"""
    print("\n🔍 Testing Critical Endpoints")
    print("=" * 40)
    
    endpoints = [
        ("/", "Home page"),
        ("/item-master", "Item Master page"),
        ("/packing/", "Packing page"),
        ("/production/", "Production page"),
        ("/inventory/", "Inventory page"),
        ("/soh/", "SOH page"),
    ]
    
    results = []
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"http://localhost:5000{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {description}: Working")
                results.append(True)
            else:
                print(f"❌ {description}: Status {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"❌ {description}: Error - {e}")
            results.append(False)
    
    return all(results)

def test_download_endpoints():
    """Test download endpoints"""
    print("\n🔍 Testing Download Endpoints")
    print("=" * 40)
    
    download_endpoints = [
        ("/item-master/download-excel", "Item Master Excel"),
        ("/item-master/download-template", "Item Master Template"),
        ("/recipe/download_recipe_excel", "Recipe Excel"),
        ("/recipe/download_recipe_template", "Recipe Template"),
        ("/soh/download_template", "SOH Template"),
        ("/ingredients/ingredients_download_template", "Ingredients Template"),
    ]
    
    results = []
    for endpoint, description in download_endpoints:
        try:
            response = requests.get(f"http://localhost:5000{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {description}: Working")
                results.append(True)
            else:
                print(f"❌ {description}: Status {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"❌ {description}: Error - {e}")
            results.append(False)
    
    return all(results)

def check_hardcoded_values():
    """Check for critical hardcoded values"""
    print("\n🔍 Checking for Critical Hardcoded Values")
    print("=" * 40)
    
    critical_files = ['app.py', 'database.py']
    issues_found = []
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Check for critical patterns
            patterns = [
                (r'root\s*:\s*[^@\s]+@', 'Database credentials'),
                (r'password\s*=\s*["\'][^"\']+["\']', 'Hardcoded password'),
                (r'secret\s*=\s*["\'][^"\']+["\']', 'Hardcoded secret'),
                (r'german', 'Hardcoded password value'),
                (r'gbdb', 'Hardcoded database name'),
                (r'mysql\+mysqlconnector://', 'Hardcoded database URL'),
            ]
            
            for pattern, description in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    issues_found.append(f"{file_path}: {description}")
    
    if issues_found:
        print("❌ Critical hardcoded values found:")
        for issue in issues_found:
            print(f"  - {issue}")
        return False
    else:
        print("✅ No critical hardcoded values found")
        return True

def generate_summary():
    """Generate a summary of the test results"""
    print("\n📊 Test Summary")
    print("=" * 40)
    
    # Test application status
    app_running = test_application_status()
    
    if app_running:
        # Test endpoints
        endpoints_working = test_critical_endpoints()
        downloads_working = test_download_endpoints()
        
        # Check hardcoded values
        no_hardcoded = check_hardcoded_values()
        
        # Summary
        print(f"\n📋 Results Summary:")
        print(f"  Application Running: {'✅' if app_running else '❌'}")
        print(f"  Critical Endpoints: {'✅' if endpoints_working else '❌'}")
        print(f"  Download Endpoints: {'✅' if downloads_working else '❌'}")
        print(f"  No Hardcoded Values: {'✅' if no_hardcoded else '❌'}")
        
        if all([app_running, endpoints_working, downloads_working, no_hardcoded]):
            print(f"\n🎉 All tests passed! Application is working correctly.")
        else:
            print(f"\n⚠️ Some tests failed. Please review the issues above.")
    else:
        print(f"\n❌ Application is not running. Please start the application first.")

if __name__ == '__main__':
    print("🚀 GB-APP Quick Test")
    print("=" * 40)
    generate_summary() 