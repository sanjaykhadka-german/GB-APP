#!/usr/bin/env python3
"""
Hardcoded Values Checker for GB-APP
Systematically checks for hardcoded values across the entire project
"""

import os
import re
import json
from pathlib import Path

class HardcodedValuesChecker:
    """Checker for hardcoded values in the project"""
    
    def __init__(self):
        self.project_root = Path('.')
        self.hardcoded_issues = []
        self.sensitive_patterns = [
            # Database credentials
            r'root\s*:\s*[^@\s]+@',
            r'password\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            
            # URLs and endpoints
            r'localhost:\d+',
            r'127\.0\.0\.1:\d+',
            r'http://[^"\']+',
            r'https://[^"\']+',
            
            # File paths
            r'C:\\[^"\']+',
            r'/home/[^"\']+',
            r'/Users/[^"\']+',
            
            # Email addresses
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            
            # IP addresses
            r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            
            # Development keys
            r'dev\s*=\s*["\'][^"\']+["\']',
            r'debug\s*=\s*True',
            
            # Specific hardcoded values found in the project
            r'german',
            r'gbdb',
            r'mysql\+mysqlconnector://',
        ]
        
        self.ignore_patterns = [
            r'venv/',
            r'__pycache__/',
            r'\.git/',
            r'\.pyc$',
            r'\.log$',
            r'\.sqlite$',
            r'\.db$',
            r'node_modules/',
            r'\.env',
            r'\.gitignore',
            r'README',
            r'requirements\.txt',
            r'\.md$',
        ]
    
    def should_ignore_file(self, file_path):
        """Check if file should be ignored"""
        file_str = str(file_path)
        for pattern in self.ignore_patterns:
            if re.search(pattern, file_str, re.IGNORECASE):
                return True
        return False
    
    def check_file(self, file_path):
        """Check a single file for hardcoded values"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            issues = []
            for pattern in self.sensitive_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    issues.append({
                        'pattern': pattern,
                        'matches': matches,
                        'file': str(file_path)
                    })
            
            return issues
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return []
    
    def scan_project(self):
        """Scan the entire project for hardcoded values"""
        print("🔍 Scanning project for hardcoded values...")
        
        # Get all Python files
        python_files = list(self.project_root.rglob('*.py'))
        html_files = list(self.project_root.rglob('*.html'))
        js_files = list(self.project_root.rglob('*.js'))
        css_files = list(self.project_root.rglob('*.css'))
        
        all_files = python_files + html_files + js_files + css_files
        
        # Filter out ignored files
        files_to_check = [f for f in all_files if not self.should_ignore_file(f)]
        
        print(f"Found {len(files_to_check)} files to check")
        
        for file_path in files_to_check:
            issues = self.check_file(file_path)
            self.hardcoded_issues.extend(issues)
    
    def generate_report(self):
        """Generate a comprehensive report"""
        print("\n" + "=" * 60)
        print("📋 HARDCODED VALUES REPORT")
        print("=" * 60)
        
        if not self.hardcoded_issues:
            print("✅ No hardcoded values found!")
            return
        
        # Group issues by file
        issues_by_file = {}
        for issue in self.hardcoded_issues:
            file_path = issue['file']
            if file_path not in issues_by_file:
                issues_by_file[file_path] = []
            issues_by_file[file_path].append(issue)
        
        # Print report
        for file_path, issues in issues_by_file.items():
            print(f"\n📁 {file_path}")
            print("-" * 40)
            
            for issue in issues:
                pattern = issue['pattern']
                matches = issue['matches']
                
                print(f"  Pattern: {pattern}")
                print(f"  Matches: {matches[:3]}...")  # Show first 3 matches
                if len(matches) > 3:
                    print(f"  ... and {len(matches) - 3} more")
                print()
        
        # Summary
        print(f"\n📊 SUMMARY")
        print(f"Total files with issues: {len(issues_by_file)}")
        print(f"Total issues found: {len(self.hardcoded_issues)}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        print("1. Move database credentials to environment variables")
        print("2. Use configuration files for URLs and endpoints")
        print("3. Replace hardcoded secrets with environment variables")
        print("4. Use relative paths instead of absolute paths")
        print("5. Consider using a secrets management system")
    
    def check_specific_files(self):
        """Check specific critical files"""
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
        
        print("\n🔍 Checking critical files...")
        
        for file_name in critical_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                issues = self.check_file(file_path)
                if issues:
                    print(f"❌ {file_name}: {len(issues)} issues found")
                    for issue in issues:
                        print(f"   - {issue['pattern']}: {issue['matches'][:2]}")
                else:
                    print(f"✅ {file_name}: No issues found")
            else:
                print(f"⚠️  {file_name}: File not found")

def main():
    """Main function"""
    checker = HardcodedValuesChecker()
    
    print("🔍 GB-APP Hardcoded Values Checker")
    print("=" * 60)
    
    # Check specific critical files first
    checker.check_specific_files()
    
    # Scan entire project
    checker.scan_project()
    
    # Generate report
    checker.generate_report()
    
    # Save detailed report to file
    with open('hardcoded_values_report.json', 'w') as f:
        json.dump(checker.hardcoded_issues, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: hardcoded_values_report.json")

if __name__ == '__main__':
    main() 