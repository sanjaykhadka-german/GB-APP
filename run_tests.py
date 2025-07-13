#!/usr/bin/env python3
"""
Test Runner for GB-APP
Runs comprehensive tests for download buttons, search/filter functionality, and hardcoded values
"""

import subprocess
import sys
import os
import json
from datetime import datetime

def run_command(command, description):
    """Run a command and return the result"""
    print(f"\n🔄 Running: {description}")
    print(f"Command: {command}")
    print("-" * 60)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Success")
            if result.stdout:
                print("Output:")
                print(result.stdout)
        else:
            print("❌ Failed")
            if result.stderr:
                print("Error:")
                print(result.stderr)
            if result.stdout:
                print("Output:")
                print(result.stdout)
        
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        print("⏰ Timeout - command took too long")
        return False, "", "Timeout"
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False, "", str(e)

def check_application_running():
    """Check if the Flask application is running"""
    print("\n🔍 Checking if application is running...")
    
    try:
        import requests
        response = requests.get("http://localhost:5000/", timeout=5)
        if response.status_code == 200:
            print("✅ Application is running")
            return True
        else:
            print(f"⚠️ Application responded with status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Application not running: {e}")
        return False

def generate_test_report(results):
    """Generate a comprehensive test report"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = {
        "timestamp": timestamp,
        "summary": {
            "total_tests": len(results),
            "passed": sum(1 for r in results if r["success"]),
            "failed": sum(1 for r in results if not r["success"])
        },
        "results": results
    }
    
    # Save report to file
    with open("test_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests: {report['summary']['total_tests']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Success rate: {(report['summary']['passed'] / report['summary']['total_tests'] * 100):.1f}%")
    
    # Print failed tests
    failed_tests = [r for r in results if not r["success"]]
    if failed_tests:
        print(f"\n❌ FAILED TESTS:")
        for test in failed_tests:
            print(f"  - {test['description']}")
            if test['error']:
                print(f"    Error: {test['error']}")
    
    return report

def main():
    """Main test runner"""
    print("🚀 GB-APP Comprehensive Test Suite")
    print("=" * 60)
    
    # Check if application is running
    app_running = check_application_running()
    if not app_running:
        print("\n⚠️ Application is not running. Starting it...")
        # Start the application in background
        subprocess.Popen([sys.executable, "app.py"], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        
        # Wait a bit for the app to start
        import time
        time.sleep(5)
        
        # Check again
        app_running = check_application_running()
        if not app_running:
            print("❌ Could not start application. Please start it manually and run tests again.")
            return
    
    # Define tests to run
    tests = [
        {
            "command": f"{sys.executable} check_hardcoded_values.py",
            "description": "Hardcoded Values Check"
        },
        {
            "command": f"{sys.executable} test_comprehensive.py",
            "description": "Comprehensive Functionality Tests"
        }
    ]
    
    # Run tests
    results = []
    for test in tests:
        success, stdout, stderr = run_command(test["command"], test["description"])
        results.append({
            "description": test["description"],
            "success": success,
            "stdout": stdout,
            "error": stderr if not success else None
        })
    
    # Generate report
    report = generate_test_report(results)
    
    # Print final status
    if report['summary']['failed'] == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️ {report['summary']['failed']} test(s) failed. Please review the results above.")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code) 