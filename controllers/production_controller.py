from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash
from datetime import datetime, timedelta
from database import db  
from models.production import Production
from models.filling import Filling
from models.joining import Joining
from sqlalchemy.sql import text

production_bp = Blueprint('production', __name__, template_folder='templates')

@production_bp.route('/production_list', methods=['GET'])
def production_list():
    # Get search parameters from query string
    search_production_code = request.args.get('production_code', '').strip()
    search_description = request.args.get('description', '').strip()
    search_week_commencing = request.args.get('week_commencing', '').strip()
    search_production_date = request.args.get('production_date', '').strip()

    # Query productions with optional filters
    productions_query = Production.query
    if search_week_commencing:
        try:
            week_commencing_date = datetime.strptime(search_week_commencing, '%Y-%m-%d').date()
            productions_query = productions_query.filter(Production.week_commencing == week_commencing_date)
        except ValueError:
            flash("Invalid Week Commencing date format.", 'error')
    if search_production_date:
        try:
            production_date = datetime.strptime(search_production_date, '%Y-%m-%d').date()
            productions_query = productions_query.filter(Production.production_date == production_date)
        except ValueError:
            flash("Invalid Production Date format.", 'error')
    if search_production_code:
        productions_query = productions_query.filter(Production.production_code.ilike(f"%{search_production_code}%"))
    if search_description:
        productions_query = productions_query.filter(Production.description.ilike(f"%{search_description}%"))

    productions = productions_query.all()
    return render_template('production/list.html',
                         productions=productions,
                         search_production_code=search_production_code,
                         search_description=search_description,
                         search_week_commencing=search_week_commencing,
                         search_production_date=search_production_date,
                         current_page="production")

@production_bp.route('/production_create', methods=['GET', 'POST'])
def production_create():
    if request.method == 'POST':
        try:
            production_date_str = request.form['production_date']
            production_date = datetime.strptime(production_date_str, '%Y-%m-%d').date()
            production_code = request.form['production_code']
            product_description = request.form['product_description']
            #description = request.form['description']
            batches = float(request.form['batches']) if request.form.get('batches') else 0.0
            total_kg = float(request.form['total_kg']) if request.form.get('total_kg') else 0.0

            # calculate week commencing (Monday of the production date) 
            def get_week_commencing(dt):
                return dt - timedelta(days=dt.weekday())
            week_commencing = get_week_commencing(production_date)
                # Find the previous Monday (or today if it's Monday)
        
            

            # Validate production_code exists in Joining table
            joining = Joining.query.filter_by(production=production_code).first()
            if not joining:
                flash(f"No Joining record found for production code {production_code}.", 'error')
                return render_template('production/create.html',current_page="production")

            new_production = Production(
                production_date=production_date,
                production_code=production_code,
                description=product_description,
                batches=batches,
                total_kg=total_kg,
                week_commencing=week_commencing 
            )
            db.session.add(new_production)
            db.session.commit()

            flash("Production entry created successfully!", "success")
            return redirect(url_for('production.production_list'))
        except ValueError as e:
            db.session.rollback()
            flash(f"Invalid input: {str(e)}. Please check your data.", 'error')
            return render_template('production/create.html',current_page="production")
        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred: {str(e)}", 'error')
            return render_template('production/create.html',current_page="production")

    return render_template('production/create.html',current_page="production")

@production_bp.route('/production_edit/<int:id>', methods=['GET', 'POST'])
def production_edit(id):
    production = Production.query.get_or_404(id)

    if request.method == 'POST':
        try:
            production_date_str = request.form['production_date']
            production.production_date = datetime.strptime(production_date_str, '%Y-%m-%d').date()
            production.production_code = request.form['production_code']
            production.productioon_description = request.form['product_description']
            #production.description = request.form['description']
            production.batches = float(request.form['batches']) if request.form.get('batches') else 0.0
            production.total_kg = float(request.form['total_kg']) if request.form.get('total_kg') else 0.0

            # calculate week commencing (Monday of the production date)
            def get_monday_of_week(dt):
                return dt - timedelta(days=dt.weekday())
            production.week_commencing = get_monday_of_week(production.production_date)

            # Validate production_code exists in Joining table
            joining = Joining.query.filter_by(production=production.production_code).first()
            if not joining:
                flash(f"No Joining record found for production code {production.production_code}.", 'error')
                return render_template('production/edit.html', production=production,current_page="production")

            db.session.commit()
            flash("Production entry updated successfully!", "success")
            return redirect(url_for('production.production_list'))
        except ValueError as e:
            db.session.rollback()
            flash(f"Invalid input: {str(e)}. Please check your data.", 'error')
            return render_template('production/edit.html', production=production,current_page="production")
        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred: {str(e)}", 'error')
            return render_template('production/edit.html', production=production,current_page="production")

    return render_template('production/edit.html', production=production,current_page="production")

@production_bp.route('/production_delete/<int:id>', methods=['POST'])
def production_delete(id):
    production = Production.query.get_or_404(id)
    try:
        db.session.delete(production)
        db.session.commit()
        flash("Production entry deleted successfully!", "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"An unexpected error occurred: {str(e)}", 'error')
    return redirect(url_for('production.production_list'))



# Autocomplete for Production Code
@production_bp.route('/autocomplete_production', methods=['GET'])
def autocomplete_production():
    search = request.args.get('query', '').strip()

    if not search:
        return jsonify([])

    try:
        query = text("SELECT production_code, description FROM production WHERE production_code LIKE :search LIMIT 10")
        results = db.session.execute(query, {"search": f"{search}%"}).fetchall()
        suggestions = [{"production_code": row[0], "description": row[1]} for row in results]
        return jsonify(suggestions)
    except Exception as e:
        print("Error fetching production autocomplete suggestions:", e)
        return jsonify([])

# Search Productions via AJAX
@production_bp.route('/get_search_productions', methods=['GET'])
def get_search_productions():
    search_production_code = request.args.get('production_code', '').strip()
    search_description = request.args.get('description', '').strip()
    search_week_commencing = request.args.get('week_commencing', '').strip()
    search_production_date = request.args.get('production_date', '').strip()

    try:
        productions_query = Production.query

        if search_week_commencing:
            try:
                week_commencing_date = datetime.strptime(search_week_commencing, '%Y-%m-%d').date()
                productions_query = productions_query.filter(Production.week_commencing == week_commencing_date)
            except ValueError:
                return jsonify({"error": "Invalid Week Commencing date format"}), 400
        if search_production_date:
            try:
                production_date = datetime.strptime(search_production_date, '%Y-%m-%d').date()
                productions_query = productions_query.filter(Production.production_date == production_date)
            except ValueError:
                return jsonify({"error": "Invalid Production Date format"}), 400
        if search_production_code:
            productions_query = productions_query.filter(Production.production_code.ilike(f"%{search_production_code}%"))
        if search_description:
            productions_query = productions_query.filter(Production.description.ilike(f"%{search_description}%"))

        productions = productions_query.all()

        productions_data = [
            {
                "id": production.id,
                "production_date": production.production_date.strftime('%Y-%m-%d') if production.production_date else "",
                "week_commencing": production.week_commencing.strftime('%Y-%m-%d') if production.week_commencing else "",
                "production_code": production.production_code or "",
                "description": production.description or "",
                "batches": production.batches if production.batches is not None else "",
                "total_kg": production.total_kg if production.total_kg is not None else ""
            }
            for production in productions
        ]

        return jsonify(productions_data)
    except Exception as e:
        print("Error fetching search productions:", e)
        return jsonify({"error": "Failed to fetch production entries"}), 500