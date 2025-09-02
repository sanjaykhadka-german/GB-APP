from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from datetime import datetime, timedelta
from database import db
from models.filling import Filling
from models.item_master import ItemMaster
import openpyxl
from io import BytesIO

filling_bp = Blueprint('filling', __name__, template_folder='templates')

@filling_bp.route('/filling_list', methods=['GET'])
def filling_list():
    # Get search parameters from query string
    search_fill_code = request.args.get('fill_code', '').strip()
    search_description = request.args.get('description', '').strip()
    search_week_commencing = request.args.get('week_commencing', '').strip()
    search_filling_date_start = request.args.get('filling_date_start', '').strip()
    search_filling_date_end = request.args.get('filling_date_end', '').strip()

    # Query fillings with optional filters
    fillings_query = Filling.query
    if search_week_commencing:
        try:
            week_commencing_date = datetime.strptime(search_week_commencing, '%Y-%m-%d').date()
            fillings_query = fillings_query.filter(Filling.week_commencing == week_commencing_date)
        except ValueError:
            flash("Invalid Week Commencing date format.", 'error')

    # Handle date range filter
    if search_filling_date_start or search_filling_date_end:
        try:
            if search_filling_date_start:
                start_date = datetime.strptime(search_filling_date_start, '%Y-%m-%d').date()
                fillings_query = fillings_query.filter(Filling.filling_date >= start_date)
            if search_filling_date_end:
                end_date = datetime.strptime(search_filling_date_end, '%Y-%m-%d').date()
                fillings_query = fillings_query.filter(Filling.filling_date <= end_date)
                
            # Validate date range if both dates are provided
            if search_filling_date_start and search_filling_date_end:
                if start_date > end_date:
                    flash("Start date must be before or equal to end date.", 'error')
                    return render_template('filling/list.html', 
                                        filling_data=[],
                                        search_fill_code=search_fill_code,
                                        search_description=search_description,
                                        search_week_commencing=search_week_commencing,
                                        search_filling_date_start=search_filling_date_start,
                                        search_filling_date_end=search_filling_date_end,
                                        current_page="filling")
        except ValueError:
            flash("Invalid Filling Date format.", 'error')
            
    if search_fill_code:
        fillings_query = fillings_query.join(Filling.item).filter(ItemMaster.item_code.ilike(f"%{search_fill_code}%"))
    if search_description:
        fillings_query = fillings_query.join(Filling.item).filter(ItemMaster.description.ilike(f"%{search_description}%"))

    fillings = fillings_query.all()
    filling_data = [
        {
            'filling': filling,
            'week_commencing': filling.week_commencing.strftime('%Y-%m-%d') if filling.week_commencing else ''
        }
        for filling in fillings
    ]

    # Calculate total kilo per size
    total_kilo_per_size = sum(filling.kilo_per_size or 0 for filling in fillings)

    return render_template('filling/list.html',
                         filling_data=filling_data,
                         total_kilo_per_size=total_kilo_per_size,
                         search_fill_code=search_fill_code,
                         search_description=search_description,
                         search_week_commencing=search_week_commencing,
                         search_filling_date_start=search_filling_date_start,
                         search_filling_date_end=search_filling_date_end,
                         current_page="filling")

@filling_bp.route('/filling_create', methods=['GET', 'POST'])
def filling_create():
    if request.method == 'POST':
        try:
            filling_date_str = request.form['filling_date']
            filling_date = datetime.strptime(filling_date_str, '%Y-%m-%d').date()
            wipf_id = int(request.form['wipf_id'])
            kilo_per_size = float(request.form['kilo_per_size']) if request.form.get('kilo_per_size') else 0.0

            # Calculate week_commencing (Monday of the week for filling_date)
            def get_monday_of_week(dt):
                return dt - timedelta(days=dt.weekday())
            week_commencing = get_monday_of_week(filling_date)

            # Validate WIPF item exists
            wipf_item = ItemMaster.query.join(ItemMaster.item_type).filter(
                ItemMaster.id == wipf_id,
                ItemMaster.item_type.has(type_name='WIPF')
            ).first()
            if not wipf_item:
                flash(f"No WIPF item found with ID {wipf_id}.", 'error')
                return render_template('filling/create.html', current_page="filling")

            new_filling = Filling(
                filling_date=filling_date,
                week_commencing=week_commencing,  # Set week_commencing
                item_id=wipf_item.id,  # Use foreign key
                kilo_per_size=kilo_per_size
            )
            db.session.add(new_filling)
            db.session.commit()

            flash('Filling entry created successfully!', 'success')
            return redirect(url_for('filling.filling_list'))
        except ValueError as e:
            flash(f"Invalid data format: {str(e)}", 'error')
        except Exception as e:
            flash(f"Error creating filling entry: {str(e)}", 'error')

    # GET request: Display the form
    try:
        wipf_items = ItemMaster.query.join(ItemMaster.item_type).filter(
            ItemMaster.item_type.has(type_name='WIPF')
        ).all()
        return render_template('filling/create.html', wipf_items=wipf_items, current_page="filling")
    except Exception as e:
        flash(f"Error loading WIPF items: {str(e)}", 'error')
        return render_template('filling/create.html', wipf_items=[], current_page="filling")

@filling_bp.route('/filling_edit/<int:id>', methods=['GET', 'POST'])
def filling_edit(id):
    filling = Filling.query.get_or_404(id)

    if request.method == 'POST':
        try:
            filling_date_str = request.form['filling_date']
            filling.filling_date = datetime.strptime(filling_date_str, '%Y-%m-%d').date()
            filling.item_id = int(request.form['wipf_id'])
            filling.kilo_per_size = float(request.form['kilo_per_size']) if request.form.get('kilo_per_size') else 0.0

            # Calculate week_commencing (Monday of the week for filling_date)
            def get_monday_of_week(dt):
                return dt - timedelta(days=dt.weekday())
            filling.week_commencing = get_monday_of_week(filling.filling_date)

            # Validate WIPF item exists
            wipf_item = ItemMaster.query.join(ItemMaster.item_type).filter(
                ItemMaster.id == filling.item_id,
                ItemMaster.item_type.has(type_name='WIPF')
            ).first()
            if not wipf_item:
                flash(f"No WIPF item found with ID {filling.item_id}.", 'error')
                return render_template('filling/edit.html', filling=filling, current_page="filling")

            db.session.commit()
            flash('Filling entry updated successfully!', 'success')
            return redirect(url_for('filling.filling_list'))
        except ValueError as e:
            flash(f"Invalid data format: {str(e)}", 'error')
        except Exception as e:
            flash(f"Error updating filling entry: {str(e)}", 'error')

    # GET request: Display the form with existing data
    try:
        wipf_items = ItemMaster.query.join(ItemMaster.item_type).filter(
            ItemMaster.item_type.has(type_name='WIPF')
        ).all()
        return render_template('filling/edit.html', filling=filling, wipf_items=wipf_items, current_page="filling")
    except Exception as e:
        flash(f"Error loading WIPF items: {str(e)}", 'error')
        return render_template('filling/edit.html', filling=filling, wipf_items=[], current_page="filling")

@filling_bp.route('/filling_delete/<int:id>', methods=['POST'])
def filling_delete(id):
    filling = Filling.query.get_or_404(id)
    try:
        db.session.delete(filling)
        db.session.commit()
        flash("Filling entry deleted successfully!", "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"An unexpected error occurred: {str(e)}", 'error')
    return redirect(url_for('filling.filling_list'))

# Autocomplete for Filling Fill Code
@filling_bp.route('/autocomplete_filling', methods=['GET'])
def autocomplete_filling():
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify([])

    try:
        # Search for WIPF items that match the query
        wipf_items = ItemMaster.query.join(ItemMaster.item_type).filter(
            ItemMaster.item_type.has(type_name='WIPF'),
            ItemMaster.item_code.ilike(f"%{query}%")
        ).limit(10).all()

        suggestions = [
            {
                'id': item.id,
                'fill_code': item.item_code,
                'description': item.description
            }
            for item in wipf_items
        ]
        return jsonify(suggestions)
    except Exception as e:
        print("Error in autocomplete:", e)
        return jsonify([])

# Search Fillings via AJAX
@filling_bp.route('/get_search_fillings', methods=['GET'])
def get_search_fillings():
    search_fill_code = request.args.get('fill_code', '').strip()
    search_description = request.args.get('description', '').strip()
    search_week_commencing = request.args.get('week_commencing', '').strip()
    search_filling_date_start = request.args.get('filling_date_start', '').strip()
    search_filling_date_end = request.args.get('filling_date_end', '').strip()

    try:
        fillings_query = Filling.query

        if search_week_commencing:
            try:
                week_commencing_date = datetime.strptime(search_week_commencing, '%Y-%m-%d').date()
                fillings_query = fillings_query.filter(Filling.week_commencing == week_commencing_date)
            except ValueError:
                return jsonify({"error": "Invalid Week Commencing date format"}), 400

        # Handle date range filter
        if search_filling_date_start or search_filling_date_end:
            try:
                if search_filling_date_start:
                    start_date = datetime.strptime(search_filling_date_start, '%Y-%m-%d').date()
                    fillings_query = fillings_query.filter(Filling.filling_date >= start_date)
                if search_filling_date_end:
                    end_date = datetime.strptime(search_filling_date_end, '%Y-%m-%d').date()
                    fillings_query = fillings_query.filter(Filling.filling_date <= end_date)
            except ValueError:
                return jsonify({"error": "Invalid Filling Date format"}), 400

        if search_fill_code:
            fillings_query = fillings_query.join(Filling.item).filter(ItemMaster.item_code.ilike(f"%{search_fill_code}%"))
        if search_description:
            fillings_query = fillings_query.join(Filling.item).filter(ItemMaster.description.ilike(f"%{search_description}%"))

        fillings = fillings_query.all()

        fillings_data = [
            {
                "id": filling.id,
                "filling_date": filling.filling_date.strftime('%Y-%m-%d') if filling.filling_date else "",
                "week_commencing": filling.week_commencing.strftime('%Y-%m-%d') if filling.week_commencing else "",
                "fill_code": filling.item.item_code if filling.item else "",
                "description": filling.item.description if filling.item else "",
                "kilo_per_size": filling.kilo_per_size if filling.kilo_per_size is not None else "",
                "priority": filling.priority if filling.priority is not None else 0
            }
            for filling in fillings
        ]

        # Calculate total kilo per size
        total_kilo_per_size = sum(filling.kilo_per_size or 0 for filling in fillings)

        return jsonify({
            "fillings": fillings_data,
            "total_kilo_per_size": total_kilo_per_size
        })
    except Exception as e:
        print("Error fetching search fillings:", e)
        return jsonify({"error": "Failed to fetch filling entries"}), 500
    
# Export Fillings to Excel
@filling_bp.route('/export_fillings_excel', methods=['GET'])
def export_fillings_excel():
    search_fill_code = request.args.get('fill_code', '').strip()
    search_description = request.args.get('description', '').strip()
    search_week_commencing = request.args.get('week_commencing', '').strip()
    search_filling_date = request.args.get('filling_date', '').strip()

    try:
        fillings_query = Filling.query

        if search_week_commencing:
            try:
                week_commencing_date = datetime.strptime(search_week_commencing, '%Y-%m-%d').date()
                fillings_query = fillings_query.filter(Filling.week_commencing == week_commencing_date)
            except ValueError:
                flash("Invalid Week Commencing date format.", 'error')
                return redirect(url_for('filling.filling_list'))
        if search_filling_date:
            try:
                filling_date = datetime.strptime(search_filling_date, '%Y-%m-%d').date()
                fillings_query = fillings_query.filter(Filling.filling_date == filling_date)
            except ValueError:
                flash("Invalid Filling Date format.", 'error')
                return redirect(url_for('filling.filling_list'))
        if search_fill_code:
            fillings_query = fillings_query.join(Filling.item).filter(ItemMaster.item_code.ilike(f"%{search_fill_code}%"))
        if search_description:
            fillings_query = fillings_query.join(Filling.item).filter(ItemMaster.description.ilike(f"%{search_description}%"))

        fillings = fillings_query.all()

        # Create a new workbook and select the active sheet
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Fillings"

        # Define headers
        headers = ["ID", "Week Commencing", "Filling Date", "Fill Code", "Description", "Kilo per Size", "Priority"]
        ws.append(headers)

        # Add data rows
        for filling in fillings:
            ws.append([
                filling.id,
                filling.week_commencing.strftime('%Y-%m-%d') if filling.week_commencing else '',
                filling.filling_date.strftime('%Y-%m-%d') if filling.filling_date else '',
                filling.item.item_code if filling.item else '',
                filling.item.description if filling.item else '',
                filling.kilo_per_size if filling.kilo_per_size is not None else '',
                filling.priority if filling.priority is not None else 0
            ])

        # Create a BytesIO object to save the Excel file
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"fillings_export_{timestamp}.xlsx"

        # Send the file as a downloadable attachment
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print("Error generating Excel file:", e)
        flash(f"Error generating Excel file: {str(e)}", 'error')
        return redirect(url_for('filling.filling_list'))

@filling_bp.route('/filling_update_cell', methods=['POST'])
def update_cell():
    """Handle individual cell updates in the filling table"""
    try:
        data = request.get_json()
        filling_id = data.get('id')
        field = data.get('field')
        value = data.get('value')
        
        if not all([filling_id, field, value is not None]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Get the filling record
        filling = Filling.query.get(filling_id)
        if not filling:
            return jsonify({'success': False, 'error': 'Filling record not found'}), 404
        
        # Update the appropriate field
        if field == 'priority':
            try:
                priority_value = int(value) if value else 0
                if priority_value < 0:
                    return jsonify({'success': False, 'error': 'Priority cannot be negative'}), 400
                
                filling.priority = priority_value
                db.session.commit()
                return jsonify({'success': True, 'updates': {'priority': filling.priority}})
            except (ValueError, TypeError):
                return jsonify({'success': False, 'error': 'Invalid priority value'}), 400
        else:
            return jsonify({'success': False, 'error': f'Invalid field: {field}'}), 400
            
    except Exception as e:
        db.session.rollback()
        print(f"Error updating filling cell: {str(e)}")
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

def update_production_entry(filling_date, fill_code, fg_item, week_commencing=None):
    """
    This function is deprecated and no longer used.
    Production entries should only be created/updated based on packing requirements.
    """
    pass  # Do nothing - production entries should only come from packing