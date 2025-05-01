from flask import Blueprint, render_template, request, redirect, url_for, flash

# Create a Blueprint for SOH routes
soh_bp = Blueprint('soh', __name__, template_folder='templates')

# SOH List Route
@soh_bp.route('/soh_list', methods=['GET'])
def soh_list():
    from app import db
    from models.soh import SOH
    sohs = SOH.query.all()
    return render_template('soh/list.html', sohs=sohs)

# SOH Create Route
@soh_bp.route('/soh_create', methods=['GET', 'POST'])
def soh_create():
    from app import db
    from models.soh import SOH
    if request.method == 'POST':
        fg_code = request.form['fg_code']
        description = request.form['description']
        dispatch_boxes = float(request.form['dispatch_boxes']) if request.form.get('dispatch_boxes') else 0.0
        dispatch_units = float(request.form['dispatch_units']) if request.form.get('dispatch_units') else 0.0
        packing_boxes = float(request.form['packing_boxes']) if request.form.get('packing_boxes') else 0.0
        packing_units = float(request.form['packing_units']) if request.form.get('packing_units') else 0.0

        # Calculate totals
        soh_total_boxes = dispatch_boxes + packing_boxes
        soh_total_units = (dispatch_units * 10) + (packing_units * 10) + dispatch_boxes + packing_boxes

        new_soh = SOH(
            fg_code=fg_code,
            description=description,
            soh_total_boxes=soh_total_boxes,
            soh_total_units=soh_total_units
        )
        db.session.add(new_soh)
        db.session.commit()

        flash("SOH entry created successfully!", "success")
        return redirect(url_for('soh.soh_list'))

    return render_template('soh/create.html')

# SOH Edit Route
@soh_bp.route('/soh_edit/<int:id>', methods=['GET', 'POST'])
def soh_edit(id):
    from app import db
    from models.soh import SOH
    soh = SOH.query.get(id)

    if request.method == 'POST':
        soh.fg_code = request.form['fg_code']
        soh.description = request.form['description']
        dispatch_boxes = float(request.form['dispatch_boxes']) if request.form.get('dispatch_boxes') else 0.0
        dispatch_units = float(request.form['dispatch_units']) if request.form.get('dispatch_units') else 0.0
        packing_boxes = float(request.form['packing_boxes']) if request.form.get('packing_boxes') else 0.0
        packing_units = float(request.form['packing_units']) if request.form.get('packing_units') else 0.0

        # Calculate totals
        soh.soh_total_boxes = dispatch_boxes + packing_boxes
        soh.soh_total_units = (dispatch_units * 10) + (packing_units * 10) + dispatch_boxes + packing_boxes

        db.session.commit()
        flash("SOH entry updated successfully!", "success")
        return redirect(url_for('soh.soh_list'))

    return render_template('soh/edit.html', soh=soh)

# SOH Delete Route
@soh_bp.route('/soh_delete/<int:id>', methods=['POST'])
def soh_delete(id):
    from app import db
    from models.soh import SOH
    soh = SOH.query.get(id)

    if soh:
        db.session.delete(soh)
        db.session.commit()
        flash("SOH entry deleted successfully!", "danger")
    else:
        flash("SOH entry not found.", "warning")

    return redirect(url_for('soh.soh_list'))