from flask import Blueprint, render_template, request, redirect, url_for, flash
#from app import db  # Import db at module level
from models.joining import Joining

# Create a Blueprint for joining routes
joining_bp = Blueprint('joining', __name__, template_folder='templates')

# Joining List Route
@joining_bp.route('/joining_list', methods=['GET'])
def joining_list():
    joinings = Joining.query.all()
    return render_template('joining/list.html', joinings=joinings)

# Joining Create Route
@joining_bp.route('/joining_create', methods=['GET', 'POST'])
def joining_create():
    if request.method == 'POST':
        fg_code = request.form['fg_code']
        description = request.form['description']
        fw = 'fw' in request.form
        make_to_order = 'make_to_order' in request.form
        min_level = float(request.form['min_level']) if request.form.get('min_level') else None
        max_level = float(request.form['max_level']) if request.form.get('max_level') else None
        kg_per_unit = float(request.form['kg_per_unit']) if request.form.get('kg_per_unit') else None
        loss = float(request.form['loss']) if request.form.get('loss') else None
        filling_code = request.form.get('filling_code')
        filling_description = request.form.get('filling_description')
        production = request.form.get('production')

        new_joining = Joining(
            fg_code=fg_code,
            description=description,
            fw=fw,
            make_to_order=make_to_order,
            min_level=min_level,
            max_level=max_level,
            kg_per_unit=kg_per_unit,
            loss=loss,
            filling_code=filling_code,
            filling_description=filling_description,
            production=production
        )
        db.session.add(new_joining)
        db.session.commit()

        flash("Joining created successfully!", "success")
        return redirect(url_for('joining.joining_list'))

    return render_template('joining/create.html')

# Joining Edit Route
@joining_bp.route('/joining_edit/<int:id>', methods=['GET', 'POST'])
def joining_edit(id):
    joining = Joining.query.get(id)

    if request.method == 'POST':
        joining.fg_code = request.form['fg_code']
        joining.description = request.form['description']
        joining.fw = 'fw' in request.form
        joining.make_to_order = 'make_to_order' in request.form
        joining.min_level = float(request.form['min_level']) if request.form.get('min_level') else None
        joining.max_level = float(request.form['max_level']) if request.form.get('max_level') else None
        joining.kg_per_unit = float(request.form['kg_per_unit']) if request.form.get('kg_per_unit') else None
        joining.loss = float(request.form['loss']) if request.form.get('loss') else None
        joining.filling_code = request.form.get('filling_code')
        joining.filling_description = request.form.get('filling_description')
        joining.production = request.form.get('production')

        db.session.commit()
        flash("Joining updated successfully!", "success")
        return redirect(url_for('joining.joining_list'))

    return render_template('joining/edit.html', joining=joining)

# Joining Delete Route
@joining_bp.route('/joining_delete/<int:id>', methods=['POST'])
def joining_delete(id):
    joining = Joining.query.get(id)

    if joining:
        db.session.delete(joining)
        db.session.commit()
        flash("Joining deleted successfully!", "danger")
    else:
        flash("Joining not found.", "warning")

    return redirect(url_for('joining.joining_list'))