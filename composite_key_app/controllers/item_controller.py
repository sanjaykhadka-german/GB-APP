from flask import Blueprint, request, jsonify, flash, redirect, url_for
from app import db
from models.item_master import ItemMaster, ItemType, Category, Department, UOM
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_

item_bp = Blueprint('items', __name__)

@item_bp.route('/', methods=['GET'])
def get_items():
    """Get all items with pagination and search"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        search = request.args.get('search', '', type=str)
        item_type = request.args.get('item_type', '', type=str)
        
        query = ItemMaster.query
        
        # Apply search filter
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(or_(
                ItemMaster.item_code.like(search_pattern),
                ItemMaster.description.like(search_pattern)
            ))
        
        # Apply item type filter
        if item_type:
            query = query.join(ItemType).filter(ItemType.type_name == item_type)
        
        # Apply pagination
        items = query.order_by(ItemMaster.item_code, ItemMaster.description).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'items': [item.to_dict() for item in items.items],
            'total': items.total,
            'pages': items.pages,
            'current_page': items.page,
            'per_page': items.per_page,
            'has_next': items.has_next,
            'has_prev': items.has_prev
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@item_bp.route('/<int:item_id>', methods=['GET'])
def get_item(item_id):
    """Get a specific item by ID"""
    try:
        item = ItemMaster.query.get_or_404(item_id)
        return jsonify(item.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@item_bp.route('/by-code/<item_code>', methods=['GET'])
def get_items_by_code(item_code):
    """Get all variants of an item by item_code"""
    try:
        items = ItemMaster.find_variants_by_code(item_code)
        if not items:
            return jsonify({'error': 'No items found with that code'}), 404
        
        return jsonify({
            'items': [item.to_dict() for item in items],
            'count': len(items)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@item_bp.route('/by-code-description', methods=['GET'])
def get_item_by_code_and_description():
    """Get a specific item by item_code and description"""
    try:
        item_code = request.args.get('item_code')
        description = request.args.get('description')
        
        if not item_code or not description:
            return jsonify({'error': 'Both item_code and description are required'}), 400
        
        item = ItemMaster.find_by_code_and_description(item_code, description)
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        
        return jsonify(item.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@item_bp.route('/', methods=['POST'])
def create_item():
    """Create a new item"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['item_code', 'description', 'item_type_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if item with same code and description already exists
        existing_item = ItemMaster.find_by_code_and_description(
            data['item_code'], data['description']
        )
        if existing_item:
            return jsonify({
                'error': 'Item with this code and description already exists',
                'existing_item_id': existing_item.id
            }), 409
        
        # Create new item
        item = ItemMaster(
            item_code=data['item_code'],
            description=data['description'],
            item_type_id=data['item_type_id'],
            category_id=data.get('category_id'),
            department_id=data.get('department_id'),
            uom_id=data.get('uom_id'),
            min_stock=data.get('min_stock', 0),
            max_stock=data.get('max_stock', 0),
            is_active=data.get('is_active', True),
            price_per_kg=data.get('price_per_kg'),
            price_per_uom=data.get('price_per_uom'),
            is_make_to_order=data.get('is_make_to_order', False),
            loss_percentage=data.get('loss_percentage', 0),
            calculation_factor=data.get('calculation_factor', 1),
            wip_item_id=data.get('wip_item_id'),
            wipf_item_id=data.get('wipf_item_id'),
            supplier_name=data.get('supplier_name')
        )
        
        db.session.add(item)
        db.session.commit()
        
        return jsonify({
            'message': 'Item created successfully',
            'item': item.to_dict()
        }), 201
        
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({'error': 'Database integrity error: ' + str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@item_bp.route('/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    """Update an existing item"""
    try:
        item = ItemMaster.query.get_or_404(item_id)
        data = request.get_json()
        
        # Check if updating code/description would create a conflict
        if 'item_code' in data or 'description' in data:
            new_code = data.get('item_code', item.item_code)
            new_description = data.get('description', item.description)
            
            # Only check for conflicts if code or description actually changed
            if new_code != item.item_code or new_description != item.description:
                existing_item = ItemMaster.find_by_code_and_description(new_code, new_description)
                if existing_item and existing_item.id != item.id:
                    return jsonify({
                        'error': 'Item with this code and description already exists',
                        'existing_item_id': existing_item.id
                    }), 409
        
        # Update fields
        for field in ['item_code', 'description', 'item_type_id', 'category_id', 
                     'department_id', 'uom_id', 'min_stock', 'max_stock', 'is_active',
                     'price_per_kg', 'price_per_uom', 'is_make_to_order', 
                     'loss_percentage', 'calculation_factor', 'wip_item_id', 
                     'wipf_item_id', 'supplier_name']:
            if field in data:
                setattr(item, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Item updated successfully',
            'item': item.to_dict()
        })
        
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({'error': 'Database integrity error: ' + str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@item_bp.route('/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    """Delete an item"""
    try:
        item = ItemMaster.query.get_or_404(item_id)
        
        # Check if item is used in recipes
        if item.components or item.used_in_recipes:
            return jsonify({
                'error': 'Cannot delete item that is used in recipes',
                'recipes_count': len(item.components) + len(item.used_in_recipes)
            }), 400
        
        # Check if item is used as WIP or WIPF in other items
        wip_usage = ItemMaster.query.filter_by(wip_item_id=item.id).count()
        wipf_usage = ItemMaster.query.filter_by(wipf_item_id=item.id).count()
        
        if wip_usage > 0 or wipf_usage > 0:
            return jsonify({
                'error': 'Cannot delete item that is referenced by other items',
                'wip_usage': wip_usage,
                'wipf_usage': wipf_usage
            }), 400
        
        db.session.delete(item)
        db.session.commit()
        
        return jsonify({'message': 'Item deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@item_bp.route('/search', methods=['GET'])
def search_items():
    """Search items by code or description"""
    try:
        search_term = request.args.get('q', '')
        limit = request.args.get('limit', 50, type=int)
        
        items = ItemMaster.search_items(search_term, limit)
        
        return jsonify({
            'items': [item.to_dict() for item in items],
            'count': len(items)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@item_bp.route('/types', methods=['GET'])
def get_item_types():
    """Get all item types"""
    try:
        item_types = ItemType.query.filter_by(is_active=True).all()
        return jsonify([{
            'id': it.id,
            'type_name': it.type_name,
            'description': it.description
        } for it in item_types])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@item_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all categories"""
    try:
        categories = Category.query.all()
        return jsonify([{
            'id': cat.id,
            'name': cat.name,
            'description': cat.description
        } for cat in categories])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@item_bp.route('/departments', methods=['GET'])
def get_departments():
    """Get all departments"""
    try:
        departments = Department.query.all()
        return jsonify([{
            'id': dept.department_id,
            'name': dept.departmentName
        } for dept in departments])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@item_bp.route('/uoms', methods=['GET'])
def get_uoms():
    """Get all UOMs"""
    try:
        uoms = UOM.query.all()
        return jsonify([{
            'id': uom.UOMID,
            'name': uom.uom_name,
            'description': uom.description
        } for uom in uoms])
    except Exception as e:
        return jsonify({'error': str(e)}), 500