import os
import re

def fix_imports():
    files_to_check = [
        'verify_truncate.py',
        'run_migration.py',
        'force_truncate.py',
        'execute_schema_fix.py',
        'controllers/bom_service.py',
        'controllers/recipe_controller.py'
    ]
    
    old_import = 'from models.usage_report import UsageReport'
    new_import = 'from models.usage_report_table import UsageReportTable'
    old_class = r'\bUsageReport\b'
    new_class = 'UsageReportTable'
    
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            print(f"Skipping {file_path} - file not found")
            continue
            
        print(f"\nProcessing {file_path}...")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace imports and class names
        content = content.replace(old_import, new_import)
        content = re.sub(old_class, new_class, content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Updated {file_path}")

if __name__ == '__main__':
    fix_imports() 