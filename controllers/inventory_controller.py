from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db, Inventory, ItemMaster, RawMaterialReport, RawMaterialStocktake
from sqlalchemy import func
from datetime import datetime

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/inventory/')
def list_inventory():
    try:
        # Get search parameters
        search_item = request.args.get('item', '').strip()
        search_category = request.args.get('category', '').strip()
        search_week_commencing = request.args.get('week_commencing', '').strip()

        # Base query with joins
        query = db.session.query(
            Inventory, ItemMaster, RawMaterialReport, RawMaterialStocktake
        ).join(
            ItemMaster, Inventory.item_id == ItemMaster.id
        ).outerjoin(
            RawMaterialReport, 
            (RawMaterialReport.item_id == ItemMaster.id) & 
            (RawMaterialReport.week_commencing == Inventory.week_commencing)
        ).outerjoin(
            RawMaterialStocktake,
            RawMaterialStocktake.item_id == ItemMaster.id
        )

        # Apply filters
        if search_item:
            query = query.filter(ItemMaster.description.ilike(f'%{search_item}%'))
        if search_category:
            query = query.filter(ItemMaster.category_id == search_category)
        if search_week_commencing:
            query = query.filter(Inventory.week_commencing == search_week_commencing)

        # Get categories for filter dropdown
        categories = db.session.query(ItemMaster.category_id, ItemMaster.category).distinct().all()

        # Execute query
        results = query.all()

        # Process results
        inventories = []
        for inv, item, report, stocktake in results:
            # Update inventory with latest data
            inv.required_total = report.usage if report else 0
            inv.price_per_kg = item.price_per_kg
            inv.current_stock = stocktake.current_stock if stocktake else 0
            inv.supplier_name = item.supplier_name
            
            # Calculate derived values
            inv.calculate_daily_values()
            
            # Add to list
            inventories.append(inv)

        # Commit changes
        db.session.commit()

        return render_template('inventory/list.html', 
                             inventories=inventories,
                             categories=categories)
    except Exception as e:
        print(f"Error in list_inventory: {str(e)}")
        db.session.rollback()
        return render_template('inventory/list.html', 
                             inventories=[],
                             categories=[])

@inventory_bp.route('/inventory/create', methods=['GET', 'POST'])
def create_inventory():
    if request.method == 'POST':
        try:
            # Get form data
            item_id = request.form.get('item_id')
            week_commencing = datetime.strptime(request.form.get('week_commencing'), '%Y-%m-%d')

            # Create new inventory
            inventory = Inventory(
                item_id=item_id,
                week_commencing=week_commencing
            )

            # Add and commit
            db.session.add(inventory)
            db.session.commit()

            flash('Inventory created successfully', 'success')
            return redirect(url_for('inventory.list_inventory'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating inventory: {str(e)}', 'error')

    # Get items for dropdown
    items = ItemMaster.query.all()
    return render_template('inventory/create.html', items=items)

@inventory_bp.route('/inventory/edit/<int:id>', methods=['GET', 'POST'])
def edit_inventory(id):
    inventory = Inventory.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Update fields
            inventory.item_id = request.form.get('item_id')
            inventory.week_commencing = datetime.strptime(request.form.get('week_commencing'), '%Y-%m-%d')
            
            # Update daily values
            for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
                for field in ['required_kg', 'to_be_ordered', 'ordered_received', 'consumed_kg']:
                    field_name = f"{day}_{field}"
                    value = request.form.get(field_name, 0)
                    setattr(inventory, field_name, float(value) if value else 0)

            # Recalculate all values
            inventory.calculate_daily_values()
            
            # Save changes
            db.session.commit()
            flash('Inventory updated successfully', 'success')
            return redirect(url_for('inventory.list_inventory'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating inventory: {str(e)}', 'error')

    items = ItemMaster.query.all()
    return render_template('inventory/edit.html', inventory=inventory, items=items)

@inventory_bp.route('/inventory/update_field', methods=['POST'])
def update_inventory_field():
    try:
        data = request.get_json()
        inventory_id = data.get('id')
        field = data.get('field')
        value = float(data.get('value', 0))

        inventory = Inventory.query.get_or_404(inventory_id)
        
        # Update the specified field
        setattr(inventory, field, value)
        
        # Recalculate all values
        inventory.calculate_daily_values()
        
        # Save changes
        db.session.commit()

        # Get the day from the field name
        day = field.split('_')[0]

        # Return updated values
        return jsonify({
            'success': True,
            'data': {
                'required_for_plan': round(inventory.required_for_plan, 2),
                'variance_for_week': round(inventory.variance_for_week, 2),
                'value_required': round(inventory.value_required, 2),
                'opening_stock': round(getattr(inventory, f"{day}_opening_stock"), 2),
                'variance': round(getattr(inventory, f"{day}_variance"), 2),
                'closing_stock': round(getattr(inventory, f"{day}_closing_stock"), 2)
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@inventory_bp.route('/inventory/delete/<int:id>', methods=['POST'])
def delete_inventory(id):
    try:
        inventory = Inventory.query.get_or_404(id)
        db.session.delete(inventory)
        db.session.commit()
        flash('Inventory deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting inventory: {str(e)}', 'error')
    return redirect(url_for('inventory.list_inventory'))