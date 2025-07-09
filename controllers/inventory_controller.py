from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from database import db
from models.inventory import Inventory
from models.item_master import ItemMaster
from models.category import Category
from models.item_type import ItemType
from datetime import datetime

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/')
def list_inventory():
    try:
        inventories = Inventory.query.all()
        categories = Category.query.all()
        return render_template('inventory/list.html', inventories=inventories, categories=categories)
    except Exception as e:
        print(f"Error in list_inventory: {str(e)}")
        flash('Error loading inventory list', 'error')
        return render_template('inventory/list.html', inventories=[], categories=[])

@inventory_bp.route('/create', methods=['GET', 'POST'])
def create_inventory():
    if request.method == 'POST':
        try:
            inventory = Inventory(
                week_commencing=datetime.strptime(request.form['week_commencing'], '%Y-%m-%d').date(),
                item_id=request.form['item_id'],
                category_id=request.form['category_id'],
                price_per_kg=request.form['price_per_kg'],
                required_total_production=request.form['required_total_production'],
                value_required_rm=request.form['value_required_rm'],
                current_stock=request.form['current_stock'],
                required_for_plan=request.form['required_for_plan'],
                variance_week=request.form['variance_week'],
                kg_required=request.form['kg_required'],
                variance=request.form['variance'],
                to_be_ordered=request.form['to_be_ordered'],
                closing_stock=request.form['closing_stock']
            )
            db.session.add(inventory)
            db.session.commit()
            flash('Inventory created successfully!', 'success')
            return redirect(url_for('inventory.list_inventory'))
        except Exception as e:
            print(f"Error in create_inventory: {str(e)}")
            db.session.rollback()
            flash('Error creating inventory', 'error')
    
    # Get RM type ID
    rm_type = ItemType.query.filter_by(type_name='RM').first()
    if not rm_type:
        flash('Error: RM item type not found', 'error')
        return redirect(url_for('inventory.list_inventory'))
    
    # Get all raw materials
    items = ItemMaster.query.filter_by(item_type_id=rm_type.id).all()
    categories = Category.query.all()
    return render_template('inventory/create.html', items=items, categories=categories)

@inventory_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_inventory(id):
    inventory = Inventory.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            inventory.week_commencing = datetime.strptime(request.form['week_commencing'], '%Y-%m-%d').date()
            inventory.item_id = request.form['item_id']
            inventory.category_id = request.form['category_id']
            inventory.price_per_kg = request.form['price_per_kg']
            inventory.required_total_production = request.form['required_total_production']
            inventory.value_required_rm = request.form['value_required_rm']
            inventory.current_stock = request.form['current_stock']
            inventory.required_for_plan = request.form['required_for_plan']
            inventory.variance_week = request.form['variance_week']
            inventory.kg_required = request.form['kg_required']
            inventory.variance = request.form['variance']
            inventory.to_be_ordered = request.form['to_be_ordered']
            inventory.closing_stock = request.form['closing_stock']
            
            db.session.commit()
            flash('Inventory updated successfully!', 'success')
            return redirect(url_for('inventory.list_inventory'))
        except Exception as e:
            print(f"Error in edit_inventory: {str(e)}")
            db.session.rollback()
            flash('Error updating inventory', 'error')
    
    # Get RM type ID
    rm_type = ItemType.query.filter_by(type_name='RM').first()
    if not rm_type:
        flash('Error: RM item type not found', 'error')
        return redirect(url_for('inventory.list_inventory'))
    
    # Get all raw materials
    items = ItemMaster.query.filter_by(item_type_id=rm_type.id).all()
    categories = Category.query.all()
    return render_template('inventory/edit.html', inventory=inventory, items=items, categories=categories)

@inventory_bp.route('/delete/<int:id>', methods=['POST'])
def delete_inventory(id):
    try:
        inventory = Inventory.query.get_or_404(id)
        db.session.delete(inventory)
        db.session.commit()
        return jsonify({'message': 'Inventory deleted successfully!'})
    except Exception as e:
        print(f"Error in delete_inventory: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Error deleting inventory'}), 500

@inventory_bp.route('/api/item/<int:id>')
def get_item(id):
    try:
        item = ItemMaster.query.get_or_404(id)
        return jsonify({
            'price_per_kg': float(item.price_per_kg) if item.price_per_kg else 0,
            'category_id': item.category_id
        })
    except Exception as e:
        print(f"Error in get_item: {str(e)}")
        return jsonify({'error': 'Error getting item details'}), 500