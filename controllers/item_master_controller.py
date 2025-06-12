from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from database import db
from models.item_master import ItemMaster
from models.category import Category
from models.department import Department
from models.machinery import Machinery
from models.uom import UOM
from models.allergen import Allergen
from datetime import datetime

item_master_bp = Blueprint('item_master', __name__)

@item_master_bp.route('/item-master', methods=['GET'])
def item_master_list():
    # Get all lookup data for the filters
    categories = Category.query.all()
    departments = Department.query.all()
    
    return render_template('item_master/list.html',
                         categories=categories,
                         departments=departments,
                         current_page='item_master')

@item_master_bp.route('/item-master/create', methods=['GET'])
def item_master_create():
    # Get all lookup data
    categories = Category.query.all()
    departments = Department.query.all()
    machinery = Machinery.query.all()
    uoms = UOM.query.all()
    allergens = Allergen.query.all()
    
    return render_template('item_master/edit.html',
                         categories=categories,
                         departments=departments,
                         machinery=machinery,
                         uoms=uoms,
                         allergens=allergens,
                         item=None,
                         current_page='item_master')

@item_master_bp.route('/item-master/edit/<int:id>', methods=['GET'])
def item_master_edit(id):
    # Get the item
    item = ItemMaster.query.get_or_404(id)
    
    # Get all lookup data
    categories = Category.query.all()
    departments = Department.query.all()
    machinery = Machinery.query.all()
    uoms = UOM.query.all()
    allergens = Allergen.query.all()
    
    return render_template('item_master/edit.html',
                         categories=categories,
                         departments=departments,
                         machinery=machinery,
                         uoms=uoms,
                         allergens=allergens,
                         item=item,
                         current_page='item_master')

@item_master_bp.route('/get_items', methods=['GET'])
def get_items():
    search_code = request.args.get('item_code', '').strip()
    search_description = request.args.get('description', '').strip()
    search_type = request.args.get('item_type', '').strip()
    
    query = ItemMaster.query
    
    if search_code:
        query = query.filter(ItemMaster.item_code.ilike(f"%{search_code}%"))
    if search_description:
        query = query.filter(ItemMaster.description.ilike(f"%{search_description}%"))
    if search_type:
        query = query.filter(ItemMaster.item_type == search_type)
    
    items = query.all()
    
    items_data = []
    for item in items:
        item_data = {
            "id": item.id,
            "item_code": item.item_code,
            "description": item.description,
            "item_type": item.item_type,
            "category": item.category.name if item.category else None,
            "department": item.department.departmentName if item.department else None,
            "machinery": item.machinery.machineryName if item.machinery else None,
            "uom": item.uom.UOMName if item.uom else None,
            "min_level": item.min_level,
            "max_level": item.max_level,
            "price_per_kg": item.price_per_kg,
            "is_make_to_order": item.is_make_to_order,
            "kg_per_unit": item.kg_per_unit,
            "units_per_bag": item.units_per_bag,
            "loss_percentage": item.loss_percentage,
            "is_active": item.is_active,
            "allergens": [allergen.name for allergen in item.allergens]
        }
        items_data.append(item_data)
    
    return jsonify(items_data)

@item_master_bp.route('/item-master', methods=['POST'])
def save_item():
    try:
        data = request.get_json()
        
        # For edit case
        if data.get('id'):
            item = ItemMaster.query.get_or_404(data['id'])
        else:
            # For new item, check if item_code already exists
            if ItemMaster.query.filter_by(item_code=data['item_code']).first():
                return jsonify({'error': 'Item code already exists'}), 400
            item = ItemMaster()
        
        # Update basic fields
        item.item_code = data['item_code']
        item.description = data['description']
        item.item_type = data['item_type']
        item.category_id = data['category_id'] if data['category_id'] else None
        item.department_id = data['department_id'] if data['department_id'] else None
        item.machinery_id = data['machinery_id'] if data['machinery_id'] else None
        item.uom_id = data['uom_id'] if data['uom_id'] else None
        item.min_level = data['min_level'] if data['min_level'] else None
        item.max_level = data['max_level'] if data['max_level'] else None
        item.is_active = data['is_active']
        
        # Update type-specific fields
        if data['item_type'] == 'raw_material':
            item.price_per_kg = data['price_per_kg'] if data['price_per_kg'] else None
            # Clear finished good fields
            item.is_make_to_order = False
            item.kg_per_unit = None
            item.units_per_bag = None
            item.loss_percentage = None
        else:
            item.is_make_to_order = data['is_make_to_order']
            item.kg_per_unit = data['kg_per_unit'] if data['kg_per_unit'] else None
            item.units_per_bag = data['units_per_bag'] if data['units_per_bag'] else None
            item.loss_percentage = data['loss_percentage'] if data['loss_percentage'] else None
            # Clear raw material fields
            item.price_per_kg = None
        
        # Handle allergens
        if 'allergen_ids' in data:
            allergens = Allergen.query.filter(Allergen.allergens_id.in_(data['allergen_ids'])).all()
            item.allergens = allergens
        
        if not data.get('id'):
            db.session.add(item)
        
            db.session.commit()
        return jsonify({'message': 'Item saved successfully!', 'id': item.id}), 200
        
    except Exception as e:
            db.session.rollback()
        return jsonify({'error': str(e)}), 500

@item_master_bp.route('/delete-item/<int:id>', methods=['DELETE'])
def delete_item(id):
    try:
        item = ItemMaster.query.get_or_404(id)
        db.session.delete(item)
        db.session.commit()
        return jsonify({'message': 'Item deleted successfully!'}), 200
        except Exception as e:
            db.session.rollback()
        return jsonify({'error': str(e)}), 500