from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
import pandas as pd
from models.item_master import ItemMaster
from models.inventory import Inventory
from models.category import Category
from models.production import Production
from models.raw_material_stocktake import RawMaterialStocktake
from models.usage_report_table import UsageReportTable
from models.raw_material_report_table import RawMaterialReportTable
from models.item_type import ItemType
from database import db
from datetime import datetime, timedelta
from io import BytesIO
from sqlalchemy import func, text, and_
import logging

logger = logging.getLogger(__name__)

inventory_bp = Blueprint('inventory', __name__, template_folder='../templates')

def get_rm_type_id():
    """Helper function to get RM item type ID"""
    rm_type = ItemType.query.filter_by(type_name='RM').first()
    return rm_type.id if rm_type else None

def get_usage_data_for_item(item_id, week_commencing):
    """Get usage data for a specific item and week from usage report table"""
    try:
        # Get usage from raw_material_report_table for the week
        usage_data = RawMaterialReportTable.query.filter_by(
            raw_material_id=item_id,
            week_commencing=week_commencing
        ).first()
        
        if usage_data:
            return usage_data.meat_required or 0.0
        
        # Alternative: get from usage_report_table
        item = ItemMaster.query.get(item_id)
        if item:
            usage_report = UsageReportTable.query.filter_by(
                raw_material=item.description,
                week_commencing=week_commencing
            ).first()
            if usage_report:
                return usage_report.usage_kg or 0.0
        
        return 0.0
    except Exception as e:
        logger.error(f"Error getting usage data for item {item_id}: {str(e)}")
        return 0.0

def get_usage_data_for_monday(item_id, week_commencing):
    """Get usage data for Monday of a specific week"""
    try:
        # Calculate Monday of the week
        monday_date = week_commencing - timedelta(days=week_commencing.weekday())
        
        # Get usage from raw_material_report_table for that Monday
        usage_data = RawMaterialReportTable.query.filter_by(
            raw_material_id=item_id,
            production_date=monday_date
        ).first()
        
        if usage_data:
            return usage_data.meat_required or 0.0
        
        return 0.0
    except Exception as e:
        logger.error(f"Error getting Monday usage data for item {item_id}: {str(e)}")
        return 0.0

def get_current_stock_from_stocktake(item_code, week_commencing):
    """Get current stock from raw_material_stocktake table"""
    try:
        stocktake = RawMaterialStocktake.query.filter_by(
            item_code=item_code,
            week_commencing=week_commencing
        ).first()
        
        if stocktake:
            return stocktake.current_stock or 0.0
        
        return 0.0
    except Exception as e:
        logger.error(f"Error getting current stock for item {item_code}: {str(e)}")
        return 0.0

def calculate_inventory_data(item, week_commencing):
    """Calculate all inventory data for an item and week"""
    try:
        # C2: Required in TOTAL for production (from usage reports)
        required_total_production = get_usage_data_for_item(item.id, week_commencing)
        
        # E2: Price per kg from item master
        price_per_kg = float(item.price_per_kg or 0.0)
        
        # F2: $ Value for Required RM (C2 * E2)
        value_required_rm = required_total_production * price_per_kg
        
        # G2: Current stock from raw_material_stocktake
        current_stock = get_current_stock_from_stocktake(item.item_code, week_commencing)
        
        # H2: Supplier name from item master
        supplier_name = item.supplier_name or ""
        
        # I2: Required for plan (sum for that particular item) - using same as required_total_production for now
        required_for_plan = required_total_production
        
        # J2: Variance for the week (G2 - I2)
        variance_week = current_stock - required_for_plan
        
        # K2: KG Required (from usage for Monday)
        kg_required = get_usage_data_for_monday(item.id, week_commencing)
        
        # L2: Variance (G2 - K2)
        variance = current_stock - kg_required
        
        # M2: To Be Ordered (placeholder - logic to be defined)
        to_be_ordered = max(0, required_for_plan - current_stock)
        
        # N2: Closing Stock (placeholder - logic to be defined)
        closing_stock = current_stock + to_be_ordered - required_for_plan
        
        return {
            'required_total_production': required_total_production,
            'value_required_rm': value_required_rm,
            'current_stock': current_stock,
            'supplier_name': supplier_name,
            'required_for_plan': required_for_plan,
            'variance_week': variance_week,
            'kg_required': kg_required,
            'variance': variance,
            'to_be_ordered': to_be_ordered,
            'closing_stock': closing_stock
        }
    except Exception as e:
        logger.error(f"Error calculating inventory data for item {item.id}: {str(e)}")
        return {
            'required_total_production': 0.0,
            'value_required_rm': 0.0,
            'current_stock': 0.0,
            'supplier_name': "",
            'required_for_plan': 0.0,
            'variance_week': 0.0,
            'kg_required': 0.0,
            'variance': 0.0,
            'to_be_ordered': 0.0,
            'closing_stock': 0.0
        }

@inventory_bp.route('/inventory')
def inventory_page():
    categories = Category.query.all()
    # Get only raw materials from item_master
    rm_type_id = get_rm_type_id()
    if rm_type_id:
        raw_materials = ItemMaster.query.filter(ItemMaster.item_type_id == rm_type_id).order_by(ItemMaster.item_code).all()
    else:
        raw_materials = []
    return render_template('inventory/list.html', categories=categories, raw_materials=raw_materials, current_page='inventory')

@inventory_bp.route('/inventory/create', methods=['GET', 'POST'])
def create_inventory():
    if request.method == 'POST':
        try:
            # Extract form data
            week_commencing = datetime.strptime(request.form['week_commencing'], '%Y-%m-%d').date()
            raw_material_id = int(request.form['raw_material_id'])
            category_id = int(request.form['category_id'])
            price_per_kg = float(request.form['price_per_kg'])
            
            # Get item for calculations
            item = ItemMaster.query.get(raw_material_id)
            if not item:
                flash('Item not found!', 'error')
                return redirect(request.url)
            
            # Calculate inventory data
            calc_data = calculate_inventory_data(item, week_commencing)
            
            # Create inventory record
            inventory = Inventory(
                week_commencing=week_commencing,
                category_id=category_id,
                raw_material_id=raw_material_id,
                price_per_kg=price_per_kg,
                required_total_production=calc_data['required_total_production'],
                value_required_rm=calc_data['value_required_rm'],
                current_stock=calc_data['current_stock'],
                supplier_name=calc_data['supplier_name'],
                required_for_plan=calc_data['required_for_plan'],
                variance_week=calc_data['variance_week'],
                kg_required=calc_data['kg_required'],
                variance=calc_data['variance'],
                to_be_ordered=calc_data['to_be_ordered'],
                closing_stock=calc_data['closing_stock']
            )
            
            db.session.add(inventory)
            db.session.commit()
            flash('Inventory record created successfully!', 'success')
            return redirect(url_for('inventory.inventory_page'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating inventory record: {str(e)}', 'error')
            logger.error(f"Error creating inventory: {str(e)}")

    categories = Category.query.all()
    # Get only raw materials from item_master
    rm_type_id = get_rm_type_id()
    if rm_type_id:
        raw_materials = ItemMaster.query.filter(ItemMaster.item_type_id == rm_type_id).order_by(ItemMaster.item_code).all()
    else:
        raw_materials = []
    return render_template('inventory/create.html', categories=categories, raw_materials=raw_materials, current_page='inventory')

@inventory_bp.route('/inventory/edit/<int:id>', methods=['GET', 'POST'])
def edit_inventory(id):
    inventory = Inventory.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Update basic fields
            inventory.week_commencing = datetime.strptime(request.form['week_commencing'], '%Y-%m-%d').date()
            inventory.category_id = int(request.form['category_id'])
            inventory.raw_material_id = int(request.form['raw_material_id'])
            inventory.price_per_kg = float(request.form['price_per_kg'])
            
            # Get item for calculations
            item = ItemMaster.query.get(inventory.raw_material_id)
            if not item:
                flash('Item not found!', 'error')
                return redirect(request.url)
            
            # Recalculate inventory data
            calc_data = calculate_inventory_data(item, inventory.week_commencing)
            
            # Update calculated fields
            inventory.required_total_production = calc_data['required_total_production']
            inventory.value_required_rm = calc_data['value_required_rm']
            inventory.current_stock = calc_data['current_stock']
            inventory.supplier_name = calc_data['supplier_name']
            inventory.required_for_plan = calc_data['required_for_plan']
            inventory.variance_week = calc_data['variance_week']
            inventory.kg_required = calc_data['kg_required']
            inventory.variance = calc_data['variance']
            inventory.to_be_ordered = calc_data['to_be_ordered']
            inventory.closing_stock = calc_data['closing_stock']
            
            db.session.commit()
            flash('Inventory updated successfully!', 'success')
            return redirect(url_for('inventory.inventory_page'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating inventory record: {str(e)}', 'error')
            logger.error(f"Error updating inventory: {str(e)}")
            return redirect(request.url)

    categories = Category.query.all()
    # Get only raw materials from item_master
    rm_type_id = get_rm_type_id()
    if rm_type_id:
        raw_materials = ItemMaster.query.filter(ItemMaster.item_type_id == rm_type_id).order_by(ItemMaster.item_code).all()
    else:
        raw_materials = []
    return render_template('inventory/edit.html', inventory=inventory, categories=categories, raw_materials=raw_materials, current_page='inventory')

@inventory_bp.route('/inventory/delete/<int:id>', methods=['POST'])
def delete_inventory(id):
    inventory = Inventory.query.get_or_404(id)
    try:
        db.session.delete(inventory)
        db.session.commit()
        flash('Inventory record deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting inventory record: {str(e)}', 'error')
    return redirect(url_for('inventory.inventory_page'))

@inventory_bp.route('/inventory/get_data', methods=['GET'])
def get_inventory_data():
    try:
        # Get filter parameters
        category_id = request.args.get('category')
        raw_material_id = request.args.get('raw_material')
        week_commencing = request.args.get('week_commencing')
        
        # Base query with joins to get related data
        query = db.session.query(
            Inventory,
            Category.name.label('category_name'),
            ItemMaster.description.label('raw_material_name'),
            ItemMaster.item_code.label('item_code')
        ).join(
            Category, Inventory.category_id == Category.id
        ).join(
            ItemMaster, Inventory.raw_material_id == ItemMaster.id
        )
        
        # Apply filters
        if category_id:
            query = query.filter(Inventory.category_id == int(category_id))
        if raw_material_id:
            query = query.filter(Inventory.raw_material_id == int(raw_material_id))
        if week_commencing:
            week_date = datetime.strptime(week_commencing, '%Y-%m-%d').date()
            query = query.filter(Inventory.week_commencing == week_date)
        
        results = query.all()
        
        # Convert to list of dictionaries
        data = []
        for inventory, category_name, raw_material_name, item_code in results:
            data.append({
                'id': inventory.id,
                'week_commencing': inventory.week_commencing.strftime('%Y-%m-%d'),
                'category_name': category_name,
                'item_code': item_code,
                'raw_material_name': raw_material_name,
                'required_total_production': inventory.required_total_production,
                'price_per_kg': inventory.price_per_kg,
                'value_required_rm': inventory.value_required_rm,
                'current_stock': inventory.current_stock,
                'supplier_name': inventory.supplier_name,
                'required_for_plan': inventory.required_for_plan,
                'variance_week': inventory.variance_week,
                'kg_required': inventory.kg_required,
                'variance': inventory.variance,
                'to_be_ordered': inventory.to_be_ordered,
                'closing_stock': inventory.closing_stock
            })
        
        return jsonify({'data': data})
    except Exception as e:
        logger.error(f"Error getting inventory data: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Keep the other API endpoints for backward compatibility
@inventory_bp.route('/inventory/get_category_options', methods=['GET'])
def get_category_options():
    try:
        categories = Category.query.all()
        data = [{'id': category.id, 'name': category.name} for category in categories]
        return jsonify({'data': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/inventory/get_raw_material_options', methods=['GET'])
def get_raw_material_options():
    try:
        # Get only raw materials from item_master
        rm_type_id = get_rm_type_id()
        if rm_type_id:
            raw_materials = ItemMaster.query.filter(ItemMaster.item_type_id == rm_type_id).all()
        else:
            raw_materials = []
        data = [{'id': raw_material.id, 'name': raw_material.description or raw_material.item_code} for raw_material in raw_materials]
        return jsonify({'data': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/inventory/export_inventories', methods=['GET'])
def export_inventories():
    try:
        query = Inventory.query
        week_commencing = request.args.get('week_commencing')
        category_id = request.args.get('category')
        raw_material_id = request.args.get('raw_material')

        if week_commencing:
            try:
                week_commencing = datetime.strptime(week_commencing, '%Y-%m-%d').date()
                query = query.filter(Inventory.week_commencing == week_commencing)
            except ValueError:
                return jsonify({'error': 'Invalid week commencing date format'}), 400

        if category_id:
            query = query.filter(Inventory.category_id == int(category_id))

        if raw_material_id:
            query = query.filter(Inventory.raw_material_id == int(raw_material_id))

        inventories = query.all()
        data = [{
            'Week Commencing': inv.week_commencing.strftime('%Y-%m-%d') if inv.week_commencing else '',
            'Category': inv.category.name if inv.category else '',
            'Item Code': inv.raw_material.item_code if inv.raw_material else '',
            'Item Description': inv.raw_material.description if inv.raw_material else '',
            'Required Total Production': inv.required_total_production,
            'Price per kg': inv.price_per_kg,
            'Value Required RM': inv.value_required_rm,
            'Current Stock (SOH)': inv.current_stock,
            'Supplier Name': inv.supplier_name,
            'Required for Plan': inv.required_for_plan,
            'Variance Week': inv.variance_week,
            'KG Required': inv.kg_required,
            'Variance': inv.variance,
            'To Be Ordered': inv.to_be_ordered,
            'Closing Stock': inv.closing_stock
        } for inv in inventories]

        df = pd.DataFrame(data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Inventory', index=False)
        output.seek(0)

        return Response(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': 'attachment;filename=inventory_export.xlsx'}
        )
    except Exception as e:
        logger.error(f"Error exporting inventories: {str(e)}")
        return jsonify({'error': str(e)}), 500