from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database import db
from models import (
    Inventory, ItemMaster, RawMaterialReport, RawMaterialStocktake, 
    Category, Production, RecipeMaster, ItemType, RawMaterialReportTable
)
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from decimal import Decimal

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/inventory/initialize/<week_commencing>', methods=['POST'])
def initialize_inventory(week_commencing):
    """Initialize inventory for a given week"""
    try:
        # Parse week commencing date
        week_date = datetime.strptime(week_commencing, '%Y-%m-%d').date()
        
        # Get all raw materials
        raw_materials = db.session.query(ItemMaster).join(
            ItemType, ItemMaster.item_type_id == ItemType.id
        ).filter(
            ItemType.type_name == 'RM'
        ).all()
        
        created_count = 0
        updated_count = 0
        error_count = 0
        
        for item in raw_materials:
            try:
                # Get current stock from raw_material_stocktake
                stocktake = RawMaterialStocktake.query.filter_by(
                    item_code=item.item_code,
                    week_commencing=week_date
                ).first()
                
                # Convert decimal values to float for calculations
                price_per_kg = float(item.price_per_kg) if item.price_per_kg else 0.0
                current_stock = float(stocktake.current_stock) if stocktake and stocktake.current_stock else 0.0
                
                # Get required total from report or calculate from production plans
                report = RawMaterialReportTable.query.filter_by(
                    item_id=item.id,
                    week_commencing=week_date
                ).first()
                
                required_total = float(report.required_total_production) if report else 0.0
                
                # Calculate value required
                value_required = required_total * price_per_kg
                
                # Check if inventory already exists
                existing = Inventory.query.filter_by(
                    item_id=item.id,
                    week_commencing=week_date
                ).first()
                
                if existing:
                    # Update existing inventory
                    existing.required_total = required_total
                    existing.price_per_kg = price_per_kg
                    existing.value_required = value_required
                    existing.current_stock = current_stock
                    existing.supplier_name = item.supplier_name
                    updated_count += 1
                else:
                    # Create new inventory
                    new_inventory = Inventory(
                        week_commencing=week_date,
                        item_id=item.id,
                        required_total=required_total,
                        price_per_kg=price_per_kg,
                        value_required=value_required,
                        current_stock=current_stock,
                        supplier_name=item.supplier_name
                    )
                    db.session.add(new_inventory)
                    created_count += 1
                    
            except Exception as e:
                print(f"Error processing item {item.item_code}: {str(e)}")
                error_count += 1
                continue
        
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': f'Inventory initialized successfully. Created: {created_count}, Updated: {updated_count}, Errors: {error_count}'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in initialize_inventory: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@inventory_bp.route('/inventory/')
def list_inventory():
    try:
        # Get search parameters
        search_item = request.args.get('item', '').strip()
        search_category = request.args.get('category', '').strip()
        search_week_commencing = request.args.get('week_commencing', '').strip()

        # First get all inventory records with their related items
        query = db.session.query(Inventory).join(
            ItemMaster, Inventory.item_id == ItemMaster.id
        )

        # Apply filters
        if search_item:
            query = query.filter(ItemMaster.description.ilike(f'%{search_item}%'))
        if search_category:
            query = query.filter(ItemMaster.category_id == search_category)
        if search_week_commencing:
            query = query.filter(Inventory.week_commencing == search_week_commencing)

        # Get the inventory records
        inventory_records = query.all()

        # Get raw material reports for the same week
        raw_material_reports = {}
        if inventory_records:
            week_commencing = inventory_records[0].week_commencing
            reports = db.session.query(RawMaterialReportTable).filter(
                RawMaterialReportTable.week_commencing == week_commencing
            ).all()
            
            # Group reports by raw_material_id
            for report in reports:
                if report.raw_material_id not in raw_material_reports:
                    raw_material_reports[report.raw_material_id] = {
                        'total_required': 0.0,
                        'daily_required': {}
                    }
                raw_material_reports[report.raw_material_id]['total_required'] += report.meat_required
                raw_material_reports[report.raw_material_id]['daily_required'][report.production_date] = report.meat_required

        # Format the data for the template
        inventory_data = []
        for record in inventory_records:
            report_data = raw_material_reports.get(record.item_id, {'total_required': 0.0, 'daily_required': {}})
            
            inventory_data.append({
                'id': record.id,
                'item_code': record.item.item_code,
                'description': record.item.description,
                'required_total': report_data['total_required'],
                'price_per_kg': record.price_per_kg,
                'value_required': report_data['total_required'] * record.price_per_kg if record.price_per_kg else 0.0,
                'current_stock': record.current_stock,
                'supplier_name': record.supplier_name,
                'daily_required': report_data['daily_required']
            })

        return render_template(
            'inventory/list.html',
            inventory=inventory_data,
            search_item=search_item,
            search_category=search_category,
            search_week_commencing=search_week_commencing
        )

    except Exception as e:
        print(f"Error in list_inventory: {str(e)}")
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/inventory/create', methods=['GET', 'POST'])
def create_inventory():
    if request.method == 'POST':
        try:
            # Get form data
            data = request.form
            
            # Create new inventory
            inventory = Inventory(
                week_commencing=datetime.strptime(data['week_commencing'], '%Y-%m-%d').date(),
                item_id=data['item_id'],
                required_total=float(data['required_total'] or 0),
                price_per_kg=float(data['price_per_kg'] or 0),
                current_stock=float(data['current_stock'] or 0),
                supplier_name=data['supplier_name']
            )
            
            db.session.add(inventory)
            db.session.commit()
            
            flash('Inventory created successfully', 'success')
            return redirect(url_for('inventory.list_inventory'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating inventory: {str(e)}', 'error')
            
    # GET request - show form
    items = db.session.query(ItemMaster).all()
    return render_template('inventory/create.html', items=items)

@inventory_bp.route('/inventory/edit/<int:id>', methods=['GET', 'POST'])
def edit_inventory(id):
    inventory = db.session.query(Inventory).get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Update inventory
            data = request.form
            inventory.week_commencing = datetime.strptime(data['week_commencing'], '%Y-%m-%d').date()
            inventory.item_id = data['item_id']
            inventory.required_total = float(data['required_total'] or 0)
            inventory.price_per_kg = float(data['price_per_kg'] or 0)
            inventory.current_stock = float(data['current_stock'] or 0)
            inventory.supplier_name = data['supplier_name']
            
            db.session.commit()
            
            flash('Inventory updated successfully', 'success')
            return redirect(url_for('inventory.list_inventory'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating inventory: {str(e)}', 'error')
    
    # GET request - show form
    items = db.session.query(ItemMaster).all()
    return render_template('inventory/edit.html', inventory=inventory, items=items)

@inventory_bp.route('/inventory/update_field', methods=['POST'])
def update_inventory_field():
    try:
        data = request.get_json()
        inventory = db.session.query(Inventory).get(data['id'])
        
        if not inventory:
            return jsonify({'success': False, 'error': 'Inventory not found'})
        
        # Update the field
        updated_data = inventory.update_field(data['field'], float(data['value']))
        
        # Save changes
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': updated_data
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        })

@inventory_bp.route('/inventory/delete/<int:id>', methods=['POST'])
def delete_inventory(id):
    try:
        inventory = db.session.query(Inventory).get_or_404(id)
        db.session.delete(inventory)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Inventory deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        })