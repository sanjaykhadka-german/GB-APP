from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta  # Added timedelta for week_commencing calculation
from database import db
from models.filling import Filling
from models.joining import Joining
from models.production import Production
from sqlalchemy import func
from sqlalchemy.sql import text

filling_bp = Blueprint('filling', __name__, template_folder='templates')

@filling_bp.route('/filling_list', methods=['GET'])
def filling_list():
    # Get search parameters from query string
    search_fill_code = request.args.get('fill_code', '').strip()
    search_description = request.args.get('description', '').strip()
    search_week_commencing = request.args.get('week_commencing', '').strip()
    search_filling_date = request.args.get('filling_date', '').strip()

    # Query fillings with optional filters
    fillings_query = Filling.query
    if search_week_commencing:
        try:
            week_commencing_date = datetime.strptime(search_week_commencing, '%Y-%m-%d').date()
            fillings_query = fillings_query.filter(Filling.week_commencing == week_commencing_date)
        except ValueError:
            flash("Invalid Week Commencing date format.", 'error')

    if search_filling_date:
        try:
            filling_date = datetime.strptime(search_filling_date, '%Y-%m-%d').date()
            fillings_query = fillings_query.filter(Filling.filling_date == filling_date)
        except ValueError:
            flash("Invalid Filling Date format.", 'error')
            
    if search_fill_code:
        fillings_query = fillings_query.filter(Filling.fill_code.ilike(f"%{search_fill_code}%"))
    if search_description:
        fillings_query = fillings_query.filter(Filling.description.ilike(f"%{search_description}%"))

    fillings = fillings_query.all()
    filling_data = [
        {
            'filling': filling,
            'week_commencing': filling.week_commencing.strftime('%Y-%m-%d') if filling.week_commencing else ''  # Include week_commencing
        }
        for filling in fillings
    ]

    return render_template('filling/list.html',
                         filling_data=filling_data,
                         search_fill_code=search_fill_code,
                         search_description=search_description,
                         search_week_commencing=search_week_commencing,
                         search_filling_date=search_filling_date,
                         current_page="filling")

@filling_bp.route('/filling_create', methods=['GET', 'POST'])
def filling_create():
    if request.method == 'POST':
        try:
            filling_date_str = request.form['filling_date']
            filling_date = datetime.strptime(filling_date_str, '%Y-%m-%d').date()
            fill_code = request.form['fill_code']
            description = request.form['description']
            kilo_per_size = float(request.form['kilo_per_size']) if request.form.get('kilo_per_size') else 0.0

            # Calculate week_commencing (Monday of the week for filling_date)
            def get_monday_of_week(dt):
                return dt - timedelta(days=dt.weekday())
            week_commencing = get_monday_of_week(filling_date)

            # Validate fill_code exists in Joining table
            joining = Joining.query.filter_by(filling_code=fill_code).first()
            if not joining:
                flash(f"No Joining record found for fill_code {fill_code}.", 'error')
                return render_template('filling/create.html', current_page="filling")

            new_filling = Filling(
                filling_date=filling_date,
                week_commencing=week_commencing,  # Set week_commencing
                fill_code=fill_code,
                description=description,
                kilo_per_size=kilo_per_size
            )
            db.session.add(new_filling)
            db.session.commit()

            # Update or create corresponding Production entry
            update_production_entry(filling_date, fill_code, joining,week_commencing)

            flash("Filling entry created successfully!", "success")
            return redirect(url_for('filling.filling_list'))
        except ValueError as e:
            db.session.rollback()
            flash(f"Invalid input: {str(e)}. Please check your data.", 'error')
            return render_template('filling/create.html', current_page="filling")
        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred: {str(e)}", 'error')
            return render_template('filling/create.html', current_page="filling")

    return render_template('filling/create.html', current_page="filling")

@filling_bp.route('/filling_edit/<int:id>', methods=['GET', 'POST'])
def filling_edit(id):
    filling = Filling.query.get_or_404(id)

    if request.method == 'POST':
        try:
            filling_date_str = request.form['filling_date']
            old_filling_date = filling.filling_date
            old_fill_code = filling.fill_code
            filling.filling_date = datetime.strptime(filling_date_str, '%Y-%m-%d').date()
            filling.fill_code = request.form['fill_code']
            filling.description = request.form['description']
            filling.kilo_per_size = float(request.form['kilo_per_size']) if request.form.get('kilo_per_size') else 0.0

            # Calculate week_commencing (Monday of the week for filling_date)
            def get_monday_of_week(dt):
                return dt - timedelta(days=dt.weekday())
            filling.week_commencing = get_monday_of_week(filling.filling_date)

            # Validate fill_code exists in Joining table
            joining = Joining.query.filter_by(filling_code=filling.fill_code).first()
            if not joining:
                flash(f"No Joining record found for fill_code {filling.fill_code}.", 'error')
                return render_template('filling/edit.html', filling=filling, current_page="filling")

            db.session.commit()

            # Update or create corresponding Production entry for new values
            update_production_entry(filling.filling_date, filling.fill_code, joining,filling.week_commencing)
            # Update Production entry for old values (in case date or fill_code changed)
            old_joining = Joining.query.filter_by(filling_code=old_fill_code).first()
            if old_joining and (old_filling_date != filling.filling_date or old_fill_code != filling.fill_code):
                update_production_entry(old_filling_date, old_fill_code, old_joining,filling.week_commencing)

            flash("Filling entry updated successfully!", "success")
            return redirect(url_for('filling.filling_list'))
        except ValueError as e:
            db.session.rollback()
            flash(f"Invalid input: {str(e)}. Please check your data.", 'error')
            return render_template('filling/edit.html', filling=filling, current_page="filling")
        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred: {str(e)}", 'error')
            return render_template('filling/edit.html', filling=filling, current_page="filling")

    return render_template('filling/edit.html', filling=filling, current_page="filling")

@filling_bp.route('/filling_delete/<int:id>', methods=['POST'])
def filling_delete(id):
    filling = Filling.query.get_or_404(id)
    try:
        filling_date = filling.filling_date
        fill_code = filling.fill_code
        db.session.delete(filling)
        db.session.commit()

        # Update corresponding Production entry
        joining = Joining.query.filter_by(filling_code=fill_code).first()
        if joining:
            update_production_entry(filling_date, fill_code, joining,filling.week_commencing)

        flash("Filling entry deleted successfully!", "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"An unexpected error occurred: {str(e)}", 'error')
    return redirect(url_for('filling.filling_list'))

# Autocomplete for Filling Fill Code
@filling_bp.route('/autocomplete_filling', methods=['GET'])
def autocomplete_filling():
    search = request.args.get('query', '').strip()

    if not search:
        return jsonify([])

    try:
        query = text("SELECT fill_code, description FROM filling WHERE fill_code LIKE :search LIMIT 10")
        results = db.session.execute(query, {"search": f"{search}%"}).fetchall()
        suggestions = [{"fill_code": row[0], "description": row[1]} for row in results]
        return jsonify(suggestions)
    except Exception as e:
        print("Error fetching filling autocomplete suggestions:", e)
        return jsonify([])

# Search Fillings via AJAX
@filling_bp.route('/get_search_fillings', methods=['GET'])
def get_search_fillings():
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
                return jsonify({"error": "Invalid Week Commencing date format"}), 400
        if search_filling_date:
            try:
                filling_date = datetime.strptime(search_filling_date, '%Y-%m-%d').date()
                fillings_query = fillings_query.filter(Filling.filling_date == filling_date)
            except ValueError:
                return jsonify({"error": "Invalid Filling Date format"}), 400

        if search_fill_code:
            fillings_query = fillings_query.filter(Filling.fill_code.ilike(f"%{search_fill_code}%"))
        if search_description:
            fillings_query = fillings_query.filter(Filling.description.ilike(f"%{search_description}%"))

        fillings = fillings_query.all()

        fillings_data = [
            {
                "id": filling.id,
                "filling_date": filling.filling_date.strftime('%Y-%m-%d') if filling.filling_date else "",
                "week_commencing": filling.week_commencing.strftime('%Y-%m-%d') if filling.week_commencing else "",  
                "fill_code": filling.fill_code or "",
                "description": filling.description or "",
                "kilo_per_size": filling.kilo_per_size if filling.kilo_per_size is not None else ""
            }
            for filling in fillings
        ]

        return jsonify(fillings_data)
    except Exception as e:
        print("Error fetching search fillings:", e)
        return jsonify({"error": "Failed to fetch filling entries"}), 500

def update_production_entry(filling_date, fill_code, joining, week_commencing=None):
    """Helper function to create or update a Production entry."""
    try:
        # Get production_code and description from Joining
        production_code = joining.production
        description = joining.description

        fill_code_prefix = fill_code.split('.')[0] if '.' in fill_code else fill_code
        if len(fill_code_prefix) > 1:
            # Aggregate total_kg for all Filling entries with the same filling_date and fill_code prefix
            total_kg = db.session.query(func.sum(Filling.kilo_per_size)).filter(
                Filling.filling_date == filling_date,
                func.substring_index(Filling.fill_code, '.', 1) == fill_code_prefix
            ).scalar() or 0.0
        else:
            # Aggregate total_kg for Filling entries with matching fill_code and filling_date
            total_kg = db.session.query(func.sum(Filling.kilo_per_size)).filter(
                Filling.filling_date == filling_date,
                Filling.fill_code == fill_code
            ).scalar() or 0.0

        # If total_kg is 0, delete the Production entry if it exists
        if total_kg == 0.0:
            production = Production.query.filter_by(
                production_date=filling_date,
                production_code=production_code
            ).first()
            if production:
                db.session.delete(production)
                db.session.commit()
            return

        # Calculate batches
        batches = total_kg / 300 if total_kg > 0 else 0.0

        # Check for existing Production entry
        production = Production.query.filter_by(
            production_date=filling_date,
            production_code=production_code
        ).first()

        if production:
            # Update existing Production entry
            production.description = description
            production.total_kg = total_kg
            production.batches = batches
            production.week_commencing = week_commencing  # Set week_commencing
        else:
            # Create new Production entry
            production = Production(
                production_date=filling_date,
                production_code=production_code,
                description=description,
                batches=batches,
                total_kg=total_kg,
                week_commencing=week_commencing  # Set week_commencing
            )
            db.session.add(production)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating Production entry: {str(e)}", 'error')