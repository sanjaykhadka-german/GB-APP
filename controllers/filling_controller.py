from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime

# Create a Blueprint for filling routes
filling_bp = Blueprint('filling', __name__, template_folder='templates')

# Filling List Route
@filling_bp.route('/filling_list', methods=['GET'])
def filling_list():
    from app import db
    from models.filling import Filling
    fillings = Filling.query.all()
    return render_template('filling/list.html', fillings=fillings)

# Filling Create Route
@filling_bp.route('/filling_create', methods=['GET', 'POST'])
def filling_create():
    from app import db
    from models.filling import Filling
    if request.method == 'POST':
        try:
            filling_date_str = request.form['filling_date']
            filling_date = datetime.strptime(filling_date_str, '%Y-%m-%d').date()
            fill_code = request.form['fill_code']
            description = request.form['description']
            kilo_per_size = float(request.form['kilo_per_size']) if request.form.get('kilo_per_size') else 0.0

            new_filling = Filling(
                filling_date=filling_date,
                fill_code=fill_code,
                description=description,
                kilo_per_size=kilo_per_size
            )
            db.session.add(new_filling)
            db.session.commit()

            flash("Filling entry created successfully!", "success")
            return redirect(url_for('filling.filling_list'))
        except ValueError as e:
            db.session.rollback()
            flash(f"Invalid input: {str(e)}. Please check your data.", 'error')
            return render_template('filling/create.html')
        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred: {str(e)}", 'error')
            return render_template('filling/create.html')

    return render_template('filling/create.html')

# Filling Edit Route
@filling_bp.route('/filling_edit/<int:id>', methods=['GET', 'POST'])
def filling_edit(id):
    from app import db
    from models.filling import Filling
    filling = Filling.query.get(id)

    if not filling:
        flash("Filling entry not found.", "warning")
        return redirect(url_for('filling.filling_list'))

    if request.method == 'POST':
        try:
            filling_date_str = request.form['filling_date']
            filling.filling_date = datetime.strptime(filling_date_str, '%Y-%m-%d').date()
            filling.fill_code = request.form['fill_code']
            filling.description = request.form['description']
            filling.kilo_per_size = float(request.form['kilo_per_size']) if request.form.get('kilo_per_size') else 0.0

            db.session.commit()
            flash("Filling entry updated successfully!", "success")
            return redirect(url_for('filling.filling_list'))
        except ValueError as e:
            db.session.rollback()
            flash(f"Invalid input: {str(e)}. Please check your data.", 'error')
            return render_template('filling/edit.html', filling=filling)
        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred: {str(e)}", 'error')
            return render_template('filling/edit.html', filling=filling)

    return render_template('filling/edit.html', filling=filling)

# Filling Delete Route
@filling_bp.route('/filling_delete/<int:id>', methods=['POST'])
def filling_delete(id):
    from app import db
    from models.filling import Filling
    filling = Filling.query.get(id)

    if filling:
        db.session.delete(filling)
        db.session.commit()
        flash("Filling entry deleted successfully!", "danger")
    else:
        flash("Filling entry not found.", "warning")

    return redirect(url_for('filling.filling_list'))