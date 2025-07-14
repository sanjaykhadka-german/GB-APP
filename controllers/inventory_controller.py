from flask import Blueprint, render_template, request, jsonify, flash, send_file, redirect, url_for
import pandas as pd
import io
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
        search_item_code = request.args.get('item_code', '').strip()

        if not search_week_commencing:
            # Default to the current week if none is selected
            today = datetime.today().date()
            search_week_commencing = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
        week_date = datetime.strptime(search_week_commencing, '%Y-%m-%d').date()

        # Run the population script to ensure data is up-to-date for the selected week
        populate_inventory({week_date})

        # Query the data for the template
        query = db.session.query(Inventory).options(
            joinedload(Inventory.item).joinedload(ItemMaster.category)
        ).filter_by(week_commencing=week_date)
        if search_item_code:
            query = query.join(Inventory.item).filter(ItemMaster.item_code == search_item_code)
        inventory_records = query.all()
        categories = Category.query.all()

        return render_template(
            'inventory/list.html',
            inventory_records=inventory_records,
            categories=categories,
            search_week_commencing=search_week_commencing,
            search_item_code=search_item_code
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

@inventory_bp.route('/inventory/export')
def export_inventory():
    """Export inventory data to an Excel file."""
    search_week_commencing = request.args.get('week_commencing', '').strip()

    if not search_week_commencing:
        flash("Please select a 'Week Commencing' date to export.", 'danger')
        return redirect(url_for('inventory.list_inventory'))

    try:
        week_date = datetime.strptime(search_week_commencing, '%Y-%m-%d').date()
        
        inventory_records = db.session.query(Inventory).options(
            joinedload(Inventory.item).joinedload(ItemMaster.category)
        ).filter_by(week_commencing=week_date).all()

        if not inventory_records:
            flash("No inventory data found for the selected week.", 'info')
            return redirect(url_for('inventory.list_inventory', week_commencing=search_week_commencing))

        export_data = []
        for inv in inventory_records:
            data_row = {
                'Item': inv.item.description,
                'Category': inv.item.category.name if inv.item.category else '',
                'Required Total': inv.required_in_total,
                '$/KG': inv.price_per_kg,
                '$ Value RM': inv.value_required_rm,
                'SOH': inv.soh,
                'Supplier Name': inv.item.supplier_name or '',
                'Required for Plan': inv.monday_required_kg + inv.tuesday_required_kg + inv.wednesday_required_kg + inv.thursday_required_kg + inv.friday_required_kg + inv.saturday_required_kg + inv.sunday_required_kg,
                'Variance Week': inv.variance_week,
                'Mon Opening': inv.monday_opening_stock,
                'Mon Required': inv.monday_required_kg,
                'Mon Variance': inv.monday_variance,
                'Mon To Be Ordered': inv.monday_to_be_ordered,
                'Mon Ordered/Received': inv.monday_ordered_received,
                'Mon Consumed': inv.monday_consumed_kg,
                'Mon Closing': inv.monday_closing_stock,
                'Tue Opening': inv.tuesday_opening_stock,
                'Tue Required': inv.tuesday_required_kg,
                'Tue Variance': inv.tuesday_variance,
                'Tue To Be Ordered': inv.tuesday_to_be_ordered,
                'Tue Ordered/Received': inv.tuesday_ordered_received,
                'Tue Consumed': inv.tuesday_consumed_kg,
                'Tue Closing': inv.tuesday_closing_stock,
                'Wed Opening': inv.wednesday_opening_stock,
                'Wed Required': inv.wednesday_required_kg,
                'Wed Variance': inv.wednesday_variance,
                'Wed To Be Ordered': inv.wednesday_to_be_ordered,
                'Wed Ordered/Received': inv.wednesday_ordered_received,
                'Wed Consumed': inv.wednesday_consumed_kg,
                'Wed Closing': inv.wednesday_closing_stock,
                'Thu Opening': inv.thursday_opening_stock,
                'Thu Required': inv.thursday_required_kg,
                'Thu Variance': inv.thursday_variance,
                'Thu To Be Ordered': inv.thursday_to_be_ordered,
                'Thu Ordered/Received': inv.thursday_ordered_received,
                'Thu Consumed': inv.thursday_consumed_kg,
                'Thu Closing': inv.thursday_closing_stock,
                'Fri Opening': inv.friday_opening_stock,
                'Fri Required': inv.friday_required_kg,
                'Fri Variance': inv.friday_variance,
                'Fri To Be Ordered': inv.friday_to_be_ordered,
                'Fri Ordered/Received': inv.friday_ordered_received,
                'Fri Consumed': inv.friday_consumed_kg,
                'Fri Closing': inv.friday_closing_stock,
                'Sat Opening': inv.saturday_opening_stock,
                'Sat Required': inv.saturday_required_kg,
                'Sat Variance': inv.saturday_variance,
                'Sat To Be Ordered': inv.saturday_to_be_ordered,
                'Sat Ordered/Received': inv.saturday_ordered_received,
                'Sat Consumed': inv.saturday_consumed_kg,
                'Sat Closing': inv.saturday_closing_stock,
                'Sun Opening': inv.sunday_opening_stock,
                'Sun Required': inv.sunday_required_kg,
                'Sun Variance': inv.sunday_variance,
                'Sun To Be Ordered': inv.sunday_to_be_ordered,
                'Sun Ordered/Received': inv.sunday_ordered_received,
                'Sun Consumed': inv.sunday_consumed_kg,
                'Sun Closing': inv.sunday_closing_stock,
            }
            export_data.append(data_row)

        df = pd.DataFrame(export_data)
        
        output = io.BytesIO()
        df.to_excel(output, index=False, sheet_name='Inventory')
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'inventory_{search_week_commencing}.xlsx'
        )
    except Exception as e:
        flash(f"An error occurred while exporting: {str(e)}", 'danger')
        return redirect(url_for('inventory.list_inventory', week_commencing=search_week_commencing))


@inventory_bp.route('/inventory/search_item_codes', methods=['GET'])
def search_item_codes():
    """Search for item codes with auto-suggestion"""
    from flask import session
    # Check if user is authenticated
    if 'user_id' not in session:
        return jsonify([]), 401
    term = request.args.get('term', '')
    if not term or len(term) < 2:
        return jsonify([])
    try:
        items = ItemMaster.query.filter(ItemMaster.item_code.ilike(f'%{term}%')).limit(10).all()
        results = [{
            'item_code': item.item_code,
            'description': item.description or ''
        } for item in items]
        return jsonify(results)
    except Exception as e:
        return jsonify([]), 500