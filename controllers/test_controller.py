from flask import Blueprint, render_template, request, jsonify
from database import db
from models import ItemMaster, RecipeMaster, ItemType
from sqlalchemy.orm import aliased

# Create a Blueprint for test routes
test_bp = Blueprint('test', __name__, template_folder='templates')

@test_bp.route('/test')
def test_page():
    """Render the test page with recipe calculator functionality."""
    try:
        # Get WIP items for the dropdown (these are the production codes/recipes)
        wip_items = db.session.query(ItemMaster).join(
            ItemType, ItemMaster.item_type_id == ItemType.id
        ).filter(
            ItemType.type_name == 'WIP'
        ).order_by(ItemMaster.item_code).all()
        
        return render_template('test.html', wip_items=wip_items)
        
    except Exception as e:
        return render_template('test.html', wip_items=[], error=str(e))

@test_bp.route('/test/get_recipe_data')
def get_recipe_data():
    """API endpoint to get recipe data for a specific production code (WIP item)."""
    try:
        production_code_id = request.args.get('production_code')
        
        if not production_code_id:
            return jsonify({'error': 'Production code ID is required'}), 400
        
        # Get the WIP item
        wip_item = ItemMaster.query.get(production_code_id)
        if not wip_item:
            return jsonify({'error': 'Production code not found'}), 404
        
        # Verify it's a WIP item
        if not wip_item.item_type or wip_item.item_type.type_name != 'WIP':
            return jsonify({'error': 'Selected item is not a WIP item'}), 400
        
        # Get recipe components for this WIP item
        recipe_components = db.session.query(
            RecipeMaster,
            ItemMaster.item_code.label('component_code'),
            ItemMaster.description.label('component_description')
        ).join(
            ItemMaster, RecipeMaster.component_item_id == ItemMaster.id
        ).filter(
            RecipeMaster.recipe_wip_id == production_code_id
        ).all()
        
        if not recipe_components:
            return jsonify({'error': f'No recipe components found for {wip_item.item_code}'}), 404
        
        # Format the response
        components_data = []
        for recipe, component_code, component_description in recipe_components:
            components_data.append({
                'component_code': component_code,
                'component_description': component_description,
                'quantity_kg': float(recipe.quantity_kg) if recipe.quantity_kg else 0.0
            })
        
        return jsonify({
            'wip_item_code': wip_item.item_code,
            'wip_item_description': wip_item.description,
            'recipe_components': components_data
        })
        
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@test_bp.route('/test/export_recipe')
def export_recipe():
    """Export recipe data to Excel or PDF (future enhancement)."""
    try:
        # This could be implemented to export the calculated recipe to Excel/PDF
        # For now, just return a success message
        return jsonify({'message': 'Export functionality will be implemented in future versions'})
        
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500 