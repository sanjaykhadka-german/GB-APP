import re

# Read the BOM service file
with open("controllers/bom_service.py", "r", encoding="utf-8") as f:
    content = f.read()

# Fix the create_usage_report method
# Replace the problematic line
content = content.replace(
    "recipe = RecipeMaster.query.filter_by(wip_item_id=wip_item.id).first()",
    "recipes = RecipeMaster.query.filter_by(recipe_wip_id=wip_item.id).all()"
)

# Fix the method to get FG item first, then WIP
old_start = """    @staticmethod
    def create_usage_report(item_id, week_commencing, requirement_kg, requirement_units):
        \"\"\"Create usage report entries for a production requirement\"\"\"
        try:
            # Get the WIP item and its recipe
            wip_item = ItemMaster.query.get(item_id)"""

new_start = """    @staticmethod
    def create_usage_report(item_id, week_commencing, requirement_kg, requirement_units):
        \"\"\"Create usage report entries for a production requirement\"\"\"
        try:
            # Get the FG item and its WIP component
            fg_item = ItemMaster.query.get(item_id)
            if not fg_item or not fg_item.wip_item_id:
                print(f\"No WIP component found for FG item {item_id}\")
                return None
                
            wip_item = ItemMaster.query.get(fg_item.wip_item_id)"""

content = content.replace(old_start, new_start)

# Fix the recipe loop
old_loop = """            # Create usage report entries for each raw material
            usage_reports = []
            for component in recipe.components:
                if not component.raw_material:
                    continue
                    
                # Calculate usage based on recipe percentage
                usage_kg = (requirement_kg * component.percentage / 100) if component.percentage else 0
                
                # Create or update usage report
                usage_report = UsageReportTable(
                    week_commencing=week_commencing,
                    production_date=week_commencing,
                    recipe_code=recipe.recipe_code,
                    raw_material=component.raw_material.item_code,
                    usage_kg=usage_kg,
                    percentage=component.percentage
                )
                
                db.session.add(usage_report)
                usage_reports.append(usage_report)
                
                # Create raw material report entry
                raw_material_report = RawMaterialReportTable(
                    production_date=week_commencing,
                    week_commencing=week_commencing,
                    raw_material=component.raw_material.item_code,
                    meat_required=usage_kg,
                    raw_material_id=component.raw_material.id
                )
                
                db.session.add(raw_material_report)"""

new_loop = """            print(f\"Found {len(recipes)} recipe components for WIP {wip_item.item_code}\")
            
            # Create usage report entries for each raw material
            usage_reports = []
            for recipe in recipes:
                component_item = ItemMaster.query.get(recipe.component_item_id)
                if not component_item:
                    continue
                    
                # Calculate usage based on recipe percentage
                usage_kg = (requirement_kg * recipe.percentage / 100) if recipe.percentage else 0
                
                print(f\"Creating usage report for {component_item.item_code}: {usage_kg} kg\")
                
                # Create usage report
                usage_report = UsageReportTable(
                    week_commencing=week_commencing,
                    production_date=week_commencing,
                    recipe_code=recipe.recipe_code,
                    raw_material=component_item.item_code,
                    usage_kg=usage_kg,
                    percentage=recipe.percentage
                )
                
                db.session.add(usage_report)
                usage_reports.append(usage_report)
                
                # Create raw material report entry
                raw_material_report = RawMaterialReportTable(
                    production_date=week_commencing,
                    week_commencing=week_commencing,
                    raw_material=component_item.item_code,
                    meat_required=usage_kg,
                    raw_material_id=component_item.id
                )
                
                db.session.add(raw_material_report)"""

content = content.replace(old_loop, new_loop)

# Fix the error conditions
content = content.replace(
    "if not recipe:",
    "if not recipes:"
)

content = content.replace(
    "print(f\"No recipe found for WIP item {wip_item.item_code}\")",
    "print(f\"No recipe components found for WIP item {wip_item.item_code}\")"
)

# Add debug output at the end
content = content.replace(
    "db.session.flush()  # Save the entries\n            return usage_reports",
    "print(f\"Created {len(usage_reports)} usage report entries\")\n            db.session.flush()  # Save the entries\n            return usage_reports"
)

# Write the fixed content back
with open("controllers/bom_service.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed BOM service create_usage_report method!")

