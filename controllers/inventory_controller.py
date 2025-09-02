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
            from sqlalchemy import or_
            query = query.join(Inventory.item).filter(
                or_(
                    ItemMaster.item_code.ilike(f'%{search_item_code}%'),
                    ItemMaster.description.ilike(f'%{search_item_code}%')
                )
            )
        inventory_records = query.all()
        categories = Category.query.all()

        # Calculate totals for each day's value ordered and value received columns
        daily_totals = {}
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        for day in days:
            daily_totals[f'{day}_value_ordered'] = sum(
                inv.price_per_kg * getattr(inv, f'{day}_to_be_ordered') for inv in inventory_records
            )
            daily_totals[f'{day}_value_received'] = sum(
                inv.price_per_kg * getattr(inv, f'{day}_ordered_received') for inv in inventory_records
            )
        
        # Calculate overall totals
        total_value_ordered = sum(daily_totals[f'{day}_value_ordered'] for day in days)
        total_value_received = sum(daily_totals[f'{day}_value_received'] for day in days)

        return render_template(
            'inventory/list.html',
            inventory_records=inventory_records,
            categories=categories,
            search_week_commencing=search_week_commencing,
            search_item_code=search_item_code,
            daily_totals=daily_totals,
            total_value_ordered=total_value_ordered,
            total_value_received=total_value_received
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

        # Get all inventory records for the same week to calculate updated totals
        week_date = inventory_item.week_commencing
        all_inventory_records = db.session.query(Inventory).options(
            joinedload(Inventory.item).joinedload(ItemMaster.category)
        ).filter_by(week_commencing=week_date).all()
        
        # Calculate updated daily totals
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        updated_daily_totals = {}
        
        for day in days:
            updated_daily_totals[f'{day}_value_ordered'] = sum(
                inv.price_per_kg * getattr(inv, f'{day}_to_be_ordered') for inv in all_inventory_records
            )
            updated_daily_totals[f'{day}_value_received'] = sum(
                inv.price_per_kg * getattr(inv, f'{day}_ordered_received') for inv in all_inventory_records
            )
        
        # Calculate other totals
        total_required_in_total = sum(inv.required_in_total for inv in all_inventory_records)
        total_value_required_rm = sum(inv.value_required_rm for inv in all_inventory_records)
        total_monday_required_kg = sum(inv.monday_required_kg for inv in all_inventory_records)
        total_tuesday_required_kg = sum(inv.tuesday_required_kg for inv in all_inventory_records)
        total_wednesday_required_kg = sum(inv.wednesday_required_kg for inv in all_inventory_records)
        total_thursday_required_kg = sum(inv.thursday_required_kg for inv in all_inventory_records)
        total_friday_required_kg = sum(inv.friday_required_kg for inv in all_inventory_records)
        total_saturday_required_kg = sum(inv.saturday_required_kg for inv in all_inventory_records)
        total_sunday_required_kg = sum(inv.sunday_required_kg for inv in all_inventory_records)

        # Prepare the updated data to send back to the frontend
        updated_data = {
            'monday_variance': inventory_item.monday_variance,
            'monday_closing_stock': inventory_item.monday_closing_stock,
            'monday_value_ordered': inventory_item.price_per_kg * inventory_item.monday_to_be_ordered,
            'monday_value_received': inventory_item.price_per_kg * inventory_item.monday_ordered_received,
            'tuesday_opening_stock': inventory_item.tuesday_opening_stock,
            'tuesday_variance': inventory_item.tuesday_variance,
            'tuesday_closing_stock': inventory_item.tuesday_closing_stock,
            'tuesday_value_ordered': inventory_item.price_per_kg * inventory_item.tuesday_to_be_ordered,
            'tuesday_value_received': inventory_item.price_per_kg * inventory_item.tuesday_ordered_received,
            'wednesday_opening_stock': inventory_item.wednesday_opening_stock,
            'wednesday_variance': inventory_item.wednesday_variance,
            'wednesday_closing_stock': inventory_item.wednesday_closing_stock,
            'wednesday_value_ordered': inventory_item.price_per_kg * inventory_item.wednesday_to_be_ordered,
            'wednesday_value_received': inventory_item.price_per_kg * inventory_item.wednesday_ordered_received,
            'thursday_opening_stock': inventory_item.thursday_opening_stock,
            'thursday_variance': inventory_item.thursday_variance,
            'thursday_closing_stock': inventory_item.thursday_closing_stock,
            'thursday_value_ordered': inventory_item.price_per_kg * inventory_item.thursday_to_be_ordered,
            'thursday_value_received': inventory_item.price_per_kg * inventory_item.thursday_ordered_received,
            'friday_opening_stock': inventory_item.friday_opening_stock,
            'friday_variance': inventory_item.friday_variance,
            'friday_closing_stock': inventory_item.friday_closing_stock,
            'friday_value_ordered': inventory_item.price_per_kg * inventory_item.friday_to_be_ordered,
            'friday_value_received': inventory_item.price_per_kg * inventory_item.friday_ordered_received,
            'saturday_opening_stock': inventory_item.saturday_opening_stock,
            'saturday_variance': inventory_item.saturday_variance,
            'saturday_closing_stock': inventory_item.saturday_closing_stock,
            'saturday_value_ordered': inventory_item.price_per_kg * inventory_item.saturday_to_be_ordered,
            'saturday_value_received': inventory_item.price_per_kg * inventory_item.saturday_ordered_received,
            'sunday_opening_stock': inventory_item.sunday_opening_stock,
            'sunday_variance': inventory_item.sunday_variance,
            'sunday_closing_stock': inventory_item.sunday_closing_stock,
            'sunday_value_ordered': inventory_item.price_per_kg * inventory_item.sunday_to_be_ordered,
            'sunday_value_received': inventory_item.price_per_kg * inventory_item.sunday_ordered_received,
            'variance_week': inventory_item.variance_week,
            # Include updated totals
            'updated_totals': {
                'required_in_total': total_required_in_total,
                'value_required_rm': total_value_required_rm,
                'monday_required_kg': total_monday_required_kg,
                'tuesday_required_kg': total_tuesday_required_kg,
                'wednesday_required_kg': total_wednesday_required_kg,
                'thursday_required_kg': total_thursday_required_kg,
                'friday_required_kg': total_friday_required_kg,
                'saturday_required_kg': total_saturday_required_kg,
                'sunday_required_kg': total_sunday_required_kg,
                **updated_daily_totals
            }
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
        from sqlalchemy import or_
        items = ItemMaster.query.filter(
            or_(
                ItemMaster.item_code.ilike(f'%{term}%'),
                ItemMaster.description.ilike(f'%{term}%')
            )
        ).limit(20).all()
        results = [{
            'item_code': item.item_code,
            'description': item.description or ''
        } for item in items]
        return jsonify(results)
    except Exception as e:
        return jsonify([]), 500