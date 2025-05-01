from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime

# Create a Blueprint for production routes
production_bp = Blueprint('production', __name__, template_folder='templates')

# Production List Route
@production_bp.route('/production_list', methods=['GET'])
def production_list():
    from app import db
    from models.production import Production
    productions = Production.query.all()
    return render_template('production/list.html', productions=productions)

# Production Create Route
@production_bp.route('/production_create', methods=['GET', 'POST'])
def production_create():
    from app import db
    from models.production import Production
    if request.method == 'POST':
        try:
            production_date_str = request.form['production_date']
            production_date = datetime.strptime(production_date_str, '%Y-%m-%d').date()
            production_code = request.form['production_code']
            description = request.form['description']
            batches = float(request.form['batches']) if request.form.get('batches') else 0.0
            total_kg = float(request.form['total_kg']) if request.form.get('total_kg') else 0.0

            new_production = Production(
                production_date=production_date,
                production_code=production_code,
                description=description,
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
            return render_template('production/create.html')
        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred: {str(e)}", 'error')
            return render_template('production/create.html')

    return render_template('production/create.html')

# Production Edit Route
@production_bp.route('/production_edit/<int:id>', methods=['GET', 'POST'])
def production_edit(id):
    from app import db
    from models.production import Production
    production = Production.query.get(id)

    if not production:
        flash("Production entry not found.", "warning")
        return redirect(url_for('production.production_list'))

    if request.method == 'POST':
        try:
            production_date_str = request.form['production_date']
            production.production_date = datetime.strptime(production_date_str, '%Y-%m-%d').date()
            production.production_code = request.form['production_code']
            production.description = request.form['description']
            production.batches = float(request.form['batches']) if request.form.get('batches') else 0.0
            production.total_kg = float(request.form['total_kg']) if request.form.get('total_kg') else 0.0

            db.session.commit()
            flash("Production entry updated successfully!", "success")
            return redirect(url_for('production.production_list'))
        except ValueError as e:
            db.session.rollback()
            flash(f"Invalid input: {str(e)}. Please check your data.", 'error')
            return render_template('production/edit.html', production=production)
        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred: {str(e)}", 'error')
            return render_template('production/edit.html', production=production)

    return render_template('production/edit.html', production=production)

# Production Delete Route
@production_bp.route('/production_delete/<int:id>', methods=['POST'])
def production_delete(id):
    from app import db
    from models.production import Production
    production = Production.query.get(id)

    if production:
        db.session.delete(production)
        db.session.commit()
        flash("Production entry deleted successfully!", "danger")
    else:
        flash("Production entry not found.", "warning")

    return redirect(url_for('production.production_list'))