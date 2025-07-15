from flask import Blueprint, request, jsonify
from app import db
from models.item_master import ItemMaster
from models.recipe_master import RecipeMaster
from sqlalchemy.exc import IntegrityError

recipe_bp = Blueprint('recipes', __name__)

@recipe_bp.route('/', methods=['GET'])
def get_recipes():
    """Get all recipes with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        wip_item_id = request.args.get('wip_item_id', type=int)
        
        query = RecipeMaster.query.filter_by(is_active=True)
        
        # Filter by WIP item if specified
        if wip_item_id:
            query = query.filter_by(recipe_wip_id=wip_item_id)
        
        recipes = query.order_by(
            RecipeMaster.recipe_wip_id, 
            RecipeMaster.sequence_number
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'recipes': [recipe.to_dict() for recipe in recipes.items],
            'total': recipes.total,
            'pages': recipes.pages,
            'current_page': recipes.page,
            'per_page': recipes.per_page,
            'has_next': recipes.has_next,
            'has_prev': recipes.has_prev
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@recipe_bp.route('/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    """Get a specific recipe component by ID"""
    try:
        recipe = RecipeMaster.query.get_or_404(recipe_id)
        return jsonify(recipe.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@recipe_bp.route('/wip/<int:wip_item_id>', methods=['GET'])
def get_recipe_for_wip(wip_item_id):
    """Get complete recipe for a WIP item"""
    try:
        wip_item = ItemMaster.query.get_or_404(wip_item_id)
        
        # Verify it's a WIP item
        if wip_item.item_type.type_name != 'WIP':
            return jsonify({'error': 'Item is not a WIP item'}), 400
        
        components = RecipeMaster.get_recipe_components(wip_item_id)
        total_weight = RecipeMaster.calculate_total_recipe_weight(wip_item_id)
        
        return jsonify({
            'wip_item': wip_item.to_dict(),
            'components': [comp.to_dict() for comp in components],
            'total_weight': total_weight,
            'component_count': len(components)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@recipe_bp.route('/component/<int:component_item_id>/usage', methods=['GET'])
def get_component_usage(component_item_id):
    """Get all recipes that use a specific component"""
    try:
        component_item = ItemMaster.query.get_or_404(component_item_id)
        usage = RecipeMaster.get_component_usage(component_item_id)
        
        return jsonify({
            'component_item': component_item.to_dict(),
            'used_in_recipes': [recipe.to_dict() for recipe in usage],
            'usage_count': len(usage)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@recipe_bp.route('/', methods=['POST'])
def create_recipe_component():
    """Create a new recipe component"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['recipe_wip_id', 'component_item_id', 'quantity_kg']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate that recipe_wip_id is actually a WIP item
        wip_item = ItemMaster.query.get(data['recipe_wip_id'])
        if not wip_item:
            return jsonify({'error': 'WIP item not found'}), 404
        
        if wip_item.item_type.type_name != 'WIP':
            return jsonify({'error': 'Recipe item must be of type WIP'}), 400
        
        # Validate component item exists
        component_item = ItemMaster.query.get(data['component_item_id'])
        if not component_item:
            return jsonify({'error': 'Component item not found'}), 404
        
        # Check if this component already exists in the recipe
        existing_component = RecipeMaster.query.filter_by(
            recipe_wip_id=data['recipe_wip_id'],
            component_item_id=data['component_item_id'],
            is_active=True
        ).first()
        
        if existing_component:
            return jsonify({
                'error': 'Component already exists in this recipe',
                'existing_recipe_id': existing_component.id
            }), 409
        
        # Create new recipe component
        recipe_component = RecipeMaster(
            recipe_wip_id=data['recipe_wip_id'],
            component_item_id=data['component_item_id'],
            quantity_kg=data['quantity_kg'],
            sequence_number=data.get('sequence_number', 1),
            notes=data.get('notes'),
            is_active=data.get('is_active', True)
        )
        
        # Calculate percentage
        recipe_component.calculate_percentage()
        
        db.session.add(recipe_component)
        db.session.commit()
        
        # Recalculate percentages for all components in this recipe
        recalculate_recipe_percentages(data['recipe_wip_id'])
        
        return jsonify({
            'message': 'Recipe component created successfully',
            'recipe_component': recipe_component.to_dict()
        }), 201
        
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({'error': 'Database integrity error: ' + str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@recipe_bp.route('/<int:recipe_id>', methods=['PUT'])
def update_recipe_component(recipe_id):
    """Update an existing recipe component"""
    try:
        recipe_component = RecipeMaster.query.get_or_404(recipe_id)
        data = request.get_json()
        
        # Update fields
        for field in ['quantity_kg', 'sequence_number', 'notes', 'is_active']:
            if field in data:
                setattr(recipe_component, field, data[field])
        
        # Recalculate percentage if quantity changed
        if 'quantity_kg' in data:
            recipe_component.calculate_percentage()
        
        db.session.commit()
        
        # Recalculate percentages for all components in this recipe
        if 'quantity_kg' in data:
            recalculate_recipe_percentages(recipe_component.recipe_wip_id)
        
        return jsonify({
            'message': 'Recipe component updated successfully',
            'recipe_component': recipe_component.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@recipe_bp.route('/<int:recipe_id>', methods=['DELETE'])
def delete_recipe_component(recipe_id):
    """Delete a recipe component"""
    try:
        recipe_component = RecipeMaster.query.get_or_404(recipe_id)
        wip_item_id = recipe_component.recipe_wip_id
        
        db.session.delete(recipe_component)
        db.session.commit()
        
        # Recalculate percentages for remaining components
        recalculate_recipe_percentages(wip_item_id)
        
        return jsonify({'message': 'Recipe component deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@recipe_bp.route('/wip/<int:wip_item_id>/bulk', methods=['POST'])
def create_bulk_recipe(wip_item_id):
    """Create multiple recipe components for a WIP item in bulk"""
    try:
        data = request.get_json()
        components = data.get('components', [])
        
        if not components:
            return jsonify({'error': 'No components provided'}), 400
        
        # Validate WIP item
        wip_item = ItemMaster.query.get_or_404(wip_item_id)
        if wip_item.item_type.type_name != 'WIP':
            return jsonify({'error': 'Item must be of type WIP'}), 400
        
        created_components = []
        errors = []
        
        for i, comp_data in enumerate(components):
            try:
                # Validate required fields for each component
                if 'component_item_id' not in comp_data or 'quantity_kg' not in comp_data:
                    errors.append(f"Component {i+1}: Missing required fields")
                    continue
                
                # Check if component already exists
                existing = RecipeMaster.query.filter_by(
                    recipe_wip_id=wip_item_id,
                    component_item_id=comp_data['component_item_id'],
                    is_active=True
                ).first()
                
                if existing:
                    errors.append(f"Component {i+1}: Already exists in recipe")
                    continue
                
                # Create component
                recipe_component = RecipeMaster(
                    recipe_wip_id=wip_item_id,
                    component_item_id=comp_data['component_item_id'],
                    quantity_kg=comp_data['quantity_kg'],
                    sequence_number=comp_data.get('sequence_number', i + 1),
                    notes=comp_data.get('notes'),
                    is_active=comp_data.get('is_active', True)
                )
                
                db.session.add(recipe_component)
                created_components.append(recipe_component)
                
            except Exception as e:
                errors.append(f"Component {i+1}: {str(e)}")
        
        if created_components:
            db.session.commit()
            
            # Recalculate percentages for all components
            recalculate_recipe_percentages(wip_item_id)
            
            return jsonify({
                'message': f'Created {len(created_components)} recipe components',
                'created_components': [comp.to_dict() for comp in created_components],
                'errors': errors
            }), 201
        else:
            db.session.rollback()
            return jsonify({
                'error': 'No components were created',
                'errors': errors
            }), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def recalculate_recipe_percentages(wip_item_id):
    """Recalculate percentages for all components in a recipe"""
    try:
        components = RecipeMaster.get_recipe_components(wip_item_id)
        total_weight = RecipeMaster.calculate_total_recipe_weight(wip_item_id)
        
        if total_weight > 0:
            for component in components:
                component.percentage = (float(component.quantity_kg) / total_weight) * 100
            
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e