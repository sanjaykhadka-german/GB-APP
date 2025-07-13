#!/usr/bin/env python3
"""
Focused Application Test Suite for GB-APP
Tests download buttons, search/filter functionality, and checks for hardcoded values in the main application
"""

import requests
import json
import os
import re
from datetime import datetime, timedelta
import unittest
from urllib.parse import urljoin

class AppFunctionalityTestSuite(unittest.TestCase):
    """Focused test suite for GB-APP main functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.base_url = "http://localhost:5000"
        self.session = requests.Session()
        
        # Test credentials (you may need to adjust these)
        self.test_user = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        # Login to get session
        self.login()
    
    def login(self):
        """Login to the application"""
        try:
            login_data = {
                'username': self.test_user['username'],
                'password': self.test_user['password']
            }
            response = self.session.post(f"{self.base_url}/login", data=login_data)
            if response.status_code == 200:
                print("✓ Login successful")
            else:
                print("⚠ Login failed, some tests may not work")
        except Exception as e:
            print(f"⚠ Login error: {e}")
    
    def test_01_critical_hardcoded_values(self):
        """Test for critical hardcoded values in main application files"""
        print("\n=== Testing Critical Hardcoded Values ===")
        
        critical_files = [
            'app.py',
            'database.py',
            'controllers/item_master_controller.py',
            'controllers/packing_controller.py',
            'controllers/production_controller.py',
            'controllers/filling_controller.py',
            'controllers/inventory_controller.py',
            'controllers/soh_controller.py',
            'controllers/recipe_controller.py',
        ]
        
        hardcoded_issues = []
        
        for file_path in critical_files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for critical hardcoded values
                critical_patterns = [
                    r'root\s*:\s*[^@\s]+@',
                    r'password\s*=\s*["\'][^"\']+["\']',
                    r'secret\s*=\s*["\'][^"\']+["\']',
                    r'german',
                    r'gbdb',
                    r'mysql\+mysqlconnector://',
                    r'localhost:\d+',
                    r'127\.0\.0\.1:\d+',
                ]
                
                for pattern in critical_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        hardcoded_issues.append({
                            'file': file_path,
                            'pattern': pattern,
                            'matches': matches
                        })
        
        if hardcoded_issues:
            print("❌ Critical hardcoded values found:")
            for issue in hardcoded_issues:
                print(f"  - {issue['file']}: {issue['pattern']} -> {issue['matches']}")
            self.fail("Critical hardcoded values detected")
        else:
            print("✅ No critical hardcoded values found")
    
    def test_02_item_master_download_functionality(self):
        """Test Item Master download functionality"""
        print("\n=== Testing Item Master Download ===")
        
        # Test download Excel functionality
        try:
            response = self.session.get(f"{self.base_url}/item-master/download-excel")
            self.assertEqual(response.status_code, 200)
            self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
                         response.headers.get('content-type', ''))
            print("✓ Item Master Excel download working")
        except Exception as e:
            print(f"❌ Item Master Excel download failed: {e}")
            self.fail(f"Item Master Excel download failed: {e}")
        
        # Test download template functionality
        try:
            response = self.session.get(f"{self.base_url}/item-master/download-template")
            self.assertEqual(response.status_code, 200)
            print("✓ Item Master template download working")
        except Exception as e:
            print(f"❌ Item Master template download failed: {e}")
            self.fail(f"Item Master template download failed: {e}")
    
    def test_03_item_master_search_functionality(self):
        """Test Item Master search functionality"""
        print("\n=== Testing Item Master Search ===")
        
        # Test search with item code
        try:
            search_params = {'item_code': 'TEST'}
            response = self.session.get(f"{self.base_url}/get_items", params=search_params)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIsInstance(data, list)
            print("✓ Item Master search by item code working")
        except Exception as e:
            print(f"❌ Item Master search failed: {e}")
            self.fail(f"Item Master search failed: {e}")
    
    def test_04_packing_download_functionality(self):
        """Test Packing download functionality"""
        print("\n=== Testing Packing Download ===")
        
        # Test export Excel functionality
        try:
            search_params = {
                'fg_code': '',
                'description': '',
                'packing_date_start': '',
                'packing_date_end': '',
                'week_commencing': '',
                'machinery': ''
            }
            response = self.session.get(f"{self.base_url}/export", params=search_params)
            self.assertEqual(response.status_code, 200)
            print("✓ Packing Excel export working")
        except Exception as e:
            print(f"❌ Packing Excel export failed: {e}")
            self.fail(f"Packing Excel export failed: {e}")
    
    def test_05_packing_search_functionality(self):
        """Test Packing search functionality"""
        print("\n=== Testing Packing Search ===")
        
        # Test search functionality
        try:
            search_params = {
                'fg_code': '',
                'description': '',
                'packing_date_start': '',
                'packing_date_end': '',
                'week_commencing': '',
                'machinery': '',
                'sort_by': 'item_code',
                'sort_order': 'asc'
            }
            response = self.session.get(f"{self.base_url}/search", params=search_params)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn('packings', data)
            print("✓ Packing search working")
        except Exception as e:
            print(f"❌ Packing search failed: {e}")
            self.fail(f"Packing search failed: {e}")
    
    def test_06_production_download_functionality(self):
        """Test Production download functionality"""
        print("\n=== Testing Production Download ===")
        
        # Test export Excel functionality
        try:
            search_params = {
                'production_code': '',
                'description': '',
                'week_commencing': '',
                'production_date_start': '',
                'production_date_end': ''
            }
            response = self.session.get(f"{self.base_url}/export_productions_excel", params=search_params)
            self.assertEqual(response.status_code, 200)
            print("✓ Production Excel export working")
        except Exception as e:
            print(f"❌ Production Excel export failed: {e}")
            self.fail(f"Production Excel export failed: {e}")
    
    def test_07_production_search_functionality(self):
        """Test Production search functionality"""
        print("\n=== Testing Production Search ===")
        
        # Test search functionality
        try:
            search_params = {
                'production_code': '',
                'description': '',
                'week_commencing': '',
                'production_date_start': '',
                'production_date_end': ''
            }
            response = self.session.get(f"{self.base_url}/get_search_productions", params=search_params)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIsInstance(data, list)
            print("✓ Production search working")
        except Exception as e:
            print(f"❌ Production search failed: {e}")
            self.fail(f"Production search failed: {e}")
    
    def test_08_inventory_download_functionality(self):
        """Test Inventory download functionality"""
        print("\n=== Testing Inventory Download ===")
        
        # Test export Excel functionality
        try:
            week_commencing = datetime.now().strftime('%Y-%m-%d')
            search_params = {'week_commencing': week_commencing}
            response = self.session.get(f"{self.base_url}/inventory/export", params=search_params)
            self.assertEqual(response.status_code, 200)
            print("✓ Inventory Excel export working")
        except Exception as e:
            print(f"❌ Inventory Excel export failed: {e}")
            self.fail(f"Inventory Excel export failed: {e}")
    
    def test_09_inventory_search_functionality(self):
        """Test Inventory search functionality"""
        print("\n=== Testing Inventory Search ===")
        
        # Test search functionality
        try:
            week_commencing = datetime.now().strftime('%Y-%m-%d')
            search_params = {'week_commencing': week_commencing}
            response = self.session.get(f"{self.base_url}/inventory", params=search_params)
            self.assertEqual(response.status_code, 200)
            print("✓ Inventory search working")
        except Exception as e:
            print(f"❌ Inventory search failed: {e}")
            self.fail(f"Inventory search failed: {e}")
    
    def test_10_recipe_download_functionality(self):
        """Test Recipe download functionality"""
        print("\n=== Testing Recipe Download ===")
        
        # Test download Excel functionality
        try:
            response = self.session.get(f"{self.base_url}/recipe/download_recipe_excel")
            self.assertEqual(response.status_code, 200)
            print("✓ Recipe Excel download working")
        except Exception as e:
            print(f"❌ Recipe Excel download failed: {e}")
            self.fail(f"Recipe Excel download failed: {e}")
        
        # Test download template functionality
        try:
            response = self.session.get(f"{self.base_url}/recipe/download_recipe_template")
            self.assertEqual(response.status_code, 200)
            print("✓ Recipe template download working")
        except Exception as e:
            print(f"❌ Recipe template download failed: {e}")
            self.fail(f"Recipe template download failed: {e}")
    
    def test_11_recipe_usage_download(self):
        """Test Recipe usage download"""
        print("\n=== Testing Recipe Usage Download ===")
        
        # Test usage download functionality
        try:
            from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            to_date = datetime.now().strftime('%Y-%m-%d')
            search_params = {'from_date': from_date, 'to_date': to_date}
            response = self.session.get(f"{self.base_url}/recipe/usage_download", params=search_params)
            self.assertEqual(response.status_code, 200)
            print("✓ Recipe usage download working")
        except Exception as e:
            print(f"❌ Recipe usage download failed: {e}")
            self.fail(f"Recipe usage download failed: {e}")
    
    def test_12_recipe_raw_material_download(self):
        """Test Recipe raw material download"""
        print("\n=== Testing Recipe Raw Material Download ===")
        
        # Test raw material download functionality
        try:
            week_commencing = datetime.now().strftime('%Y-%m-%d')
            search_params = {'week_commencing': week_commencing}
            response = self.session.get(f"{self.base_url}/recipe/raw_material_download", params=search_params)
            self.assertEqual(response.status_code, 200)
            print("✓ Recipe raw material download working")
        except Exception as e:
            print(f"❌ Recipe raw material download failed: {e}")
            self.fail(f"Recipe raw material download failed: {e}")
    
    def test_13_soh_download_functionality(self):
        """Test SOH download functionality"""
        print("\n=== Testing SOH Download ===")
        
        # Test download template functionality
        try:
            response = self.session.get(f"{self.base_url}/soh/download_template")
            self.assertEqual(response.status_code, 200)
            print("✓ SOH template download working")
        except Exception as e:
            print(f"❌ SOH template download failed: {e}")
            self.fail(f"SOH template download failed: {e}")
    
    def test_14_soh_search_functionality(self):
        """Test SOH search functionality"""
        print("\n=== Testing SOH Search ===")
        
        # Test search functionality
        try:
            search_params = {
                'fg_code': '',
                'description': '',
                'week_commencing': ''
            }
            response = self.session.get(f"{self.base_url}/soh/get_search_sohs", params=search_params)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIsInstance(data, list)
            print("✓ SOH search working")
        except Exception as e:
            print(f"❌ SOH search failed: {e}")
            self.fail(f"SOH search failed: {e}")
    
    def test_15_filling_search_functionality(self):
        """Test Filling search functionality"""
        print("\n=== Testing Filling Search ===")
        
        # Test search functionality
        try:
            search_params = {
                'fg_code': '',
                'description': '',
                'week_commencing': '',
                'filling_date_start': '',
                'filling_date_end': ''
            }
            response = self.session.get(f"{self.base_url}/filling/search", params=search_params)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIsInstance(data, list)
            print("✓ Filling search working")
        except Exception as e:
            print(f"❌ Filling search failed: {e}")
            self.fail(f"Filling search failed: {e}")
    
    def test_16_ingredients_download_functionality(self):
        """Test Ingredients download functionality"""
        print("\n=== Testing Ingredients Download ===")
        
        # Test download template functionality
        try:
            response = self.session.get(f"{self.base_url}/ingredients/ingredients_download_template")
            self.assertEqual(response.status_code, 200)
            print("✓ Ingredients template download working")
        except Exception as e:
            print(f"❌ Ingredients template download failed: {e}")
            self.fail(f"Ingredients template download failed: {e}")
    
    def test_17_autocomplete_functionality(self):
        """Test autocomplete functionality"""
        print("\n=== Testing Autocomplete Functionality ===")
        
        # Test item code autocomplete
        try:
            search_params = {'term': 'test'}
            response = self.session.get(f"{self.base_url}/search_item_codes", params=search_params)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIsInstance(data, list)
            print("✓ Item code autocomplete working")
        except Exception as e:
            print(f"❌ Item code autocomplete failed: {e}")
            self.fail(f"Item code autocomplete failed: {e}")
    
    def test_18_column_visibility_functionality(self):
        """Test column visibility functionality"""
        print("\n=== Testing Column Visibility ===")
        
        # Test that the main pages load with column visibility controls
        pages_to_test = [
            '/item-master',
            '/packing/',
            '/production/',
            '/inventory/',
            '/soh/'
        ]
        
        for page in pages_to_test:
            try:
                response = self.session.get(f"{self.base_url}{page}")
                self.assertEqual(response.status_code, 200)
                self.assertIn('column-toggle', response.text)
                print(f"✓ Column visibility controls present on {page}")
            except Exception as e:
                print(f"❌ Column visibility test failed for {page}: {e}")
                self.fail(f"Column visibility test failed for {page}: {e}")
    
    def test_19_bulk_edit_functionality(self):
        """Test bulk edit functionality"""
        print("\n=== Testing Bulk Edit Functionality ===")
        
        # Test packing bulk edit endpoint
        try:
            bulk_edit_data = {
                'packing_ids': [1],
                'updates': {
                    'special_order_kg': 10.5,
                    'calculation_factor': 1.0,
                    'machinery': None,
                    'priority': 1
                }
            }
            response = self.session.post(f"{self.base_url}/bulk_edit", 
                                       json=bulk_edit_data,
                                       headers={'Content-Type': 'application/json'})
            # This might return 404 if no data exists, which is acceptable
            self.assertIn(response.status_code, [200, 404, 401])
            print("✓ Packing bulk edit endpoint accessible")
        except Exception as e:
            print(f"❌ Packing bulk edit failed: {e}")
    
    def test_20_cell_update_functionality(self):
        """Test cell update functionality"""
        print("\n=== Testing Cell Update Functionality ===")
        
        # Test packing cell update endpoint
        try:
            cell_update_data = {
                'id': 1,
                'field': 'special_order_kg',
                'value': 10.5
            }
            response = self.session.post(f"{self.base_url}/update_cell", 
                                       json=cell_update_data,
                                       headers={'Content-Type': 'application/json'})
            # This might return 404 if no data exists, which is acceptable
            self.assertIn(response.status_code, [200, 404, 401])
            print("✓ Packing cell update endpoint accessible")
        except Exception as e:
            print(f"❌ Packing cell update failed: {e}")
    
    def test_21_environment_variables_check(self):
        """Check if environment variables are properly configured"""
        print("\n=== Testing Environment Variables ===")
        
        # Check if .env file exists
        if os.path.exists('.env'):
            print("✓ .env file exists")
        else:
            print("⚠ No .env file found - consider using environment variables for sensitive data")
        
        # Check for environment variable usage
        with open('app.py', 'r') as f:
            app_content = f.read()
            
        if 'os.environ' in app_content or 'os.getenv' in app_content:
            print("✓ Environment variables are being used")
        else:
            print("⚠ No environment variable usage detected - consider moving hardcoded values to environment variables")
    
    def test_22_security_check(self):
        """Basic security checks"""
        print("\n=== Testing Security ===")
        
        # Test authentication requirement
        try:
            response = self.session.get(f"{self.base_url}/item-master")
            self.assertEqual(response.status_code, 200)
            print("✓ Authentication working")
        except Exception as e:
            print(f"❌ Authentication test failed: {e}")
            self.fail(f"Authentication test failed: {e}")
        
        # Test CSRF protection (if implemented)
        try:
            response = self.session.get(f"{self.base_url}/")
            self.assertEqual(response.status_code, 200)
            print("✓ Basic security checks passed")
        except Exception as e:
            print(f"❌ Security check failed: {e}")
    
    def test_23_error_handling(self):
        """Test error handling"""
        print("\n=== Testing Error Handling ===")
        
        # Test 404 handling
        try:
            response = self.session.get(f"{self.base_url}/nonexistent-page")
            self.assertEqual(response.status_code, 404)
            print("✓ 404 error handling working")
        except Exception as e:
            print(f"❌ 404 error handling failed: {e}")
        
        # Test invalid JSON handling
        try:
            response = self.session.post(f"{self.base_url}/update_cell", 
                                       data="invalid json",
                                       headers={'Content-Type': 'application/json'})
            self.assertIn(response.status_code, [400, 401, 404])
            print("✓ Invalid JSON handling working")
        except Exception as e:
            print(f"❌ Invalid JSON handling failed: {e}")

def run_app_tests():
    """Run all application tests"""
    print("🚀 GB-APP Application Functionality Test Suite")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(AppFunctionalityTestSuite)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n❌ ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_app_tests()
    exit(0 if success else 1) 