from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from database import db  # Import db from database.py
from models.production import Production
from models.filling import Filling
from models.joining import Joining

production_bp = Blueprint('production', __name__, template_folder='templates')

@production_bp.route('/production_list', methods=['GET'])
def production_list():
    productions = Production.query.all()
    return render_template('production/list.html', productions=productions,current_page="production")

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
                total_kg=total_kg
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