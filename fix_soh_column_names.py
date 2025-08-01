import os

def fix_soh_controller():
    """Fix column names in SOH controller to match Excel file format"""
    
    file_path = "controllers/soh_controller.py"
    
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found!")
        return
    
    # Read the file
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Replace the mismatched column names
    replacements = [
        ("row.get(\"SOH Total Boxes\", 0)", "row.get(\"Soh_total_Box\", 0)"),
        ("row.get(\"SOH Total Units\", 0)", "row.get(\"Soh_total_Unit\", 0)"),
    ]
    
    changes_made = 0
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            changes_made += 1
            print(f"✓ Fixed: {old} → {new}")
    
    if changes_made == 0:
        print("No changes needed - column names already correct or not found")
        return
    
    # Write back the file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✓ SOH controller updated! Made {changes_made} changes.")
    print("\\nNow your code will read:")
    print("- \"Soh_total_Box\" instead of \"SOH Total Boxes\"") 
    print("- \"Soh_total_Unit\" instead of \"SOH Total Units\"")
    print("\\nThis matches your Excel file column names!")

if __name__ == "__main__":
    print("Fixing SOH Controller Column Names...")
    print("=" * 50)
    fix_soh_controller()
