import os

# Fix SOH Controller Column Names
file_path = 'controllers/soh_controller.py'

with open(file_path, 'r') as f:
    content = f.read()

# Replace column names
content = content.replace("row.get('SOH Total Boxes', 0)", "row.get('Soh_total_Box', 0)")
content = content.replace("row.get('SOH Total Units', 0)", "row.get('Soh_total_Unit', 0)")

with open(file_path, 'w') as f:
    f.write(content)

print('Column names fixed!')
