from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime

# Create a Blueprint for packing routes
packing_bp = Blueprint('packing', __name__, template_folder='templates')

# Packing List Route
@packing_bp.route('/packing_list', methods=['GET'])
def packing_list():
    from app import db
    from models.packing import Packing
    packings = Packing.query.all()
    return render_template('packing/list.html', packings=packings)

# Packing Create Route
@packing_bp.route('/packing_create', methods=['GET', 'POST'])
def packing_create():
    from app import db
    from models.packing import Packing
    if request.method == 'POST':
        try:
            packing_date_str = request.form['packing_date']
            packing_date = datetime.strptime(packing_date_str, '%Y-%m-%d').date()
            packing_code = request.form['packing_code']
            description = request.form['description']
            units = float(request.form['units']) if request.form.get('units') else 0.0
            kg = float(request.form['kg']) if request.form.get('kg') else 0.0
            adjustment_kg = float(request.form['adjustment_kg']) if request.form.get('adjustment_kg') else 0.0

            new_packing = Packing(
                packing_date=packing_date,
                packing_code=packing_code,
                description=description,
                units=units,
                kg=kg,
                adjustment_kg=adjustment_kg
            )
            db.session.add(new_packing)
            db.session.commit()

            flash("Packing entry created successfully!", "success")
            return redirect(url_for('packing.packing_list'))
        except ValueError as e:
            db.session.rollback()
            flash(f"Invalid input: {str(e)}. Please check your data.", 'error')
            return render_template('packing/create.html')
        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred: {str(e)}", 'error')
            return render_template('packing/create.html')

    return render_template('packing/create.html')

# Packing Edit Route
@packing_bp.route('/packing_edit/<int:id>', methods=['GET', 'POST'])
def packing_edit(id):
    from app import db
    from models.packing import Packing
    packing = Packing.query.get(id)

    if not packing:
        flash("Packing entry not found.", "warning")
        return redirect(url_for('packing.packing_list'))

    if request.method == 'POST':
        try:
            packing_date_str = request.form['packing_date']
            packing.packing_date = datetime.strptime(packing_date_str, '%Y-%m-%d').date()
            packing.packing_code = request.form['packing_code']
            packing.description = request.form['description']
            packing.units = float(request.form['units']) if request.form.get('units') else 0.0
            packing.kg = float(request.form['kg']) if request.form.get('kg') else 0.0
            packing.adjustment_kg = float(request.form['adjustment_kg']) if request.form.get('adjustment_kg') else 0.0

            db.session.commit()
            flash("Packing entry updated successfully!", "success")
            return redirect(url_for('packing.packing_list'))
        except ValueError as e:
            db.session.rollback()
            flash(f"Invalid input: {str(e)}. Please check your data.", 'error')
            return render_template('packing/edit.html', packing=packing)
        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred: {str(e)}", 'error')
            return render_template('packing/edit.html', packing=packing)

    return render_template('packing/edit.html', packing=packing)

# Packing Delete Route
@packing_bp.route('/packing_delete/<int:id>', methods=['POST'])
def packing_delete(id):
    from app import db
    from models.packing import Packing
    packing = Packing.query.get(id)

    if packing:
        db.session.delete(packing)
        db.session.commit()
        flash("Packing entry deleted successfully!", "danger")
    else:
        flash("Packing entry not found.", "warning")

    return redirect(url_for('packing.packing_list'))