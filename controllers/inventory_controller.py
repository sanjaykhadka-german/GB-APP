from flask import Blueprint, render_template, request, jsonify, flash
from database import db
from models import Inventory, ItemMaster, Category, Production, RecipeMaster
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta

inventory_bp = Blueprint('inventory', __name__, template_folder='templates')

def recalculate_row(inventory_item):
    """Recalculates all dependent fields for an inventory item after a user edit."""
    # Recalculate daily variances and closing stocks
    inventory_item.monday_variance = inventory_item.monday_opening_stock - inventory_item.monday_required_kg
    inventory_item.monday_closing_stock = inventory_item.monday_opening_stock + inventory_item.monday_ordered_received - inventory_item.monday_consumed_kg
    
    inventory_item.tuesday_opening_stock = inventory_item.monday_closing_stock
    inventory_item.tuesday_variance = inventory_item.tuesday_opening_stock - inventory_item.tuesday_required_kg
    inventory_item.tuesday_closing_stock = inventory_item.tuesday_opening_stock + inventory_item.tuesday_ordered_received - inventory_item.tuesday_consumed_kg

    inventory_item.wednesday_opening_stock = inventory_item.tuesday_closing_stock
    inventory_item.wednesday_variance = inventory_item.wednesday_opening_stock - inventory_item.wednesday_required_kg
    inventory_item.wednesday_closing_stock = inventory_item.wednesday_opening_stock + inventory_item.wednesday_ordered_received - inventory_item.wednesday_consumed_kg

    inventory_item.thursday_opening_stock = inventory_item.wednesday_closing_stock
    inventory_item.thursday_variance = inventory_item.thursday_opening_stock - inventory_item.thursday_required_kg
    inventory_item.thursday_closing_stock = inventory_item.thursday_opening_stock + inventory_item.thursday_ordered_received - inventory_item.thursday_consumed_kg

    inventory_item.friday_opening_stock = inventory_item.thursday_closing_stock
    inventory_item.friday_variance = inventory_item.friday_opening_stock - inventory_item.friday_required_kg
    inventory_item.friday_closing_stock = inventory_item.friday_opening_stock + inventory_item.friday_ordered_received - inventory_item.friday_consumed_kg

    inventory_item.saturday_opening_stock = inventory_item.friday_closing_stock
    inventory_item.saturday_variance = inventory_item.saturday_opening_stock - inventory_item.saturday_required_kg
    inventory_item.saturday_closing_stock = inventory_item.saturday_opening_stock + inventory_item.saturday_ordered_received - inventory_item.saturday_consumed_kg

    inventory_item.sunday_opening_stock = inventory_item.saturday_closing_stock
    inventory_item.sunday_variance = inventory_item.sunday_opening_stock - inventory_item.sunday_required_kg
    inventory_item.sunday_closing_stock = inventory_item.sunday_opening_stock + inventory_item.sunday_ordered_received - inventory_item.sunday_consumed_kg
    
    # Recalculate weekly variance
    inventory_item.variance_week = inventory_item.soh - inventory_item.required_for_plan
    
    return inventory_item


@inventory_bp.route('/inventory/')
def list_inventory():
    """Display the main inventory page."""
    from populate_inventory import populate_inventory
    try:
        search_week_commencing = request.args.get('week_commencing', '').strip()

        if not search_week_commencing:
            # Default to the current week if none is selected
            today = datetime.today().date()
            search_week_commencing = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
        
        week_date = datetime.strptime(search_week_commencing, '%Y-%m-%d').date()
        
        # Run the population script to ensure data is up-to-date for the selected week
        populate_inventory({week_date})

        # Query the data for the template
        inventory_records = db.session.query(Inventory).options(
            joinedload(Inventory.item).joinedload(ItemMaster.category)
        ).filter_by(week_commencing=week_date).all()
        
        categories = Category.query.all()

        return render_template(
            'inventory/list.html',
            inventory_records=inventory_records,
            categories=categories,
            search_week_commencing=search_week_commencing
        )
    except Exception as e:
        flash(f"Error loading inventory page: {str(e)}", 'danger')
        return render_template('inventory/list.html', inventory_records=[], categories=[])

@inventory_bp.route('/inventory/update_field', methods=['POST'])
def update_inventory_field():
    """Handle the inline editing of user-input fields."""
    try:
        data = request.get_json()
        inv_id = data.get('id')
        field = data.get('field')
        value = float(data.get('value', 0.0))

        inventory_item = db.session.query(Inventory).get(inv_id)
        if not inventory_item:
            return jsonify({'success': False, 'error': 'Inventory item not found'}), 404
        
        # Update the specific field that was edited by the user
        setattr(inventory_item, field, value)
        
        # Recalculate all dependent fields for that row
        inventory_item = recalculate_row(inventory_item)
        
        db.session.commit()

        # Prepare the updated data to send back to the frontend
        updated_data = {
            'monday_variance': inventory_item.monday_variance,
            'monday_closing_stock': inventory_item.monday_closing_stock,
            'tuesday_opening_stock': inventory_item.tuesday_opening_stock,
            'tuesday_variance': inventory_item.tuesday_variance,
            'tuesday_closing_stock': inventory_item.tuesday_closing_stock,
            'wednesday_opening_stock': inventory_item.wednesday_opening_stock,
            'wednesday_variance': inventory_item.wednesday_variance,
            'wednesday_closing_stock': inventory_item.wednesday_closing_stock,
            'thursday_opening_stock': inventory_item.thursday_opening_stock,
            'thursday_variance': inventory_item.thursday_variance,
            'thursday_closing_stock': inventory_item.thursday_closing_stock,
            'friday_opening_stock': inventory_item.friday_opening_stock,
            'friday_variance': inventory_item.friday_variance,
            'friday_closing_stock': inventory_item.friday_closing_stock,
            'saturday_opening_stock': inventory_item.saturday_closing_stock,
            'saturday_variance': inventory_item.saturday_variance,
            'saturday_closing_stock': inventory_item.saturday_closing_stock,
            'sunday_opening_stock': inventory_item.sunday_opening_stock,
            'sunday_variance': inventory_item.sunday_variance,
            'sunday_closing_stock': inventory_item.sunday_closing_stock,
            'variance_week': inventory_item.variance_week,
        }

        return jsonify({'success': True, 'data': updated_data})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500