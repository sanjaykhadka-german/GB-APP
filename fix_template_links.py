#!/usr/bin/env python3
"""
Fix Template Links
==================

Remove remaining joining table links from templates
"""

import os

def fix_template_file(file_path):
    """Fix joining links in a template file"""
    if not os.path.exists(file_path):
        return False
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Replace different variations of joining links
    replacements = [
        ('<li><a href="{{ url_for(\'joining.joining_list\') }}">Joining</a></li>', '<!-- Joining navigation removed - table deprecated -->'),
        ('<li><a href="{{ url_for(\'joining.list_joining\') }}">Joining Table</a></li>', '<!-- Joining navigation removed - table deprecated -->'),
        ('<a href="{{ url_for(\'joining.list_joining\') }}">Joining Table</a>', '<!-- Joining link removed - table deprecated -->'),
    ]
    
    for old_text, new_text in replacements:
        content = content.replace(old_text, new_text)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    return False

def main():
    """Fix all template files"""
    
    files_to_fix = [
        'templates/filling/edit.html',
        'templates/filling/create.html',
    ]
    
    fixed_count = 0
    
    for file_path in files_to_fix:
        if fix_template_file(file_path):
            print(f'✅ Fixed: {file_path}')
            fixed_count += 1
        else:
            print(f'ℹ️  No changes needed: {file_path}')
    
    print(f'\n✅ Fixed {fixed_count} template files')

if __name__ == "__main__":
    main() 