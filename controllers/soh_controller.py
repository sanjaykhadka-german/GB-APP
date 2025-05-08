from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy.sql import text
import sqlalchemy.exc

# Create a Blueprint for SOH routes
soh_bp = Blueprint('soh', __name__, template_folder='templates')

# SOH List Route
@soh_bp.route('/soh_list', methods=['GET'])
def soh_list():
    from app import db
    from models.soh import SOH

    # Get search parameters from query string
    search_fg_code = request.args.get('fg_code', '').strip()
    search_description = request.args.get('description', '').strip()

    # Query SOHs with optional filters
    sohs_query = SOH.query
    if search_fg_code:
        sohs_query = sohs_query.filter(SOH.fg_code.ilike(f"%{search_fg_code}%"))
    if search_description:
        sohs_query = sohs_query.filter(SOH.description.ilike(f"%{search_description}%"))

    sohs = sohs_query.all()

    return render_template('soh/list.html',
                         sohs=sohs,
                         search_fg_code=search_fg_code,
                         search_description=search_description)

# SOH Create Route
@soh_bp.route('/soh_create', methods=['GET', 'POST'])
def soh_create():
    from app import db
    from models.soh import SOH
    from models.finished_goods import FinishedGoods
    from models.joining import Joining

    if request.method == 'POST':
        fg_code = request.form['fg_code']
        description = request.form['description']
        dispatch_boxes = float(request.form['soh_dispatch_boxes']) if request.form.get('soh_dispatch_boxes') else 0.0
        dispatch_units = float(request.form['soh_dispatch_units']) if request.form.get('soh_dispatch_units') else 0.0
        packing_boxes = float(request.form['soh_packing_boxes']) if request.form.get('soh_packing_boxes') else 0.0
        packing_units = float(request.form['soh_packing_units']) if request.form.get('soh_packing_units') else 0.0

        # Fetch units_per_bag from FinishedGoods
        fg = Joining.query.filter_by(fg_code=fg_code).first()
        units_per_bag = fg.units_per_bag if fg and fg.units_per_bag else 1  # Default to 1 if not found

        # Calculate totals
        soh_total_boxes = dispatch_boxes + packing_boxes
        soh_total_units = (
            (dispatch_boxes * units_per_bag) +
            (packing_boxes * units_per_bag) +
            dispatch_units +
            packing_units
        )

        new_soh = SOH(
            fg_code=fg_code,
            description=description,
            soh_dispatch_boxes=dispatch_boxes,
            soh_dispatch_units=dispatch_units,
            soh_packing_boxes=packing_boxes,
            soh_packing_units=packing_units,
            soh_total_boxes=soh_total_boxes,
            soh_total_units=soh_total_units
        )
        db.session.add(new_soh)
        db.session.commit()

        flash("SOH entry created successfully!", "success")
        return redirect(url_for('soh.soh_list'))

    # GET request: Pre-fill fg_code if provided
    fg_code = request.args.get('fg_code', '')
    return render_template('soh/create.html', fg_code=fg_code)

# SOH Edit Route
@soh_bp.route('/soh_edit/<int:id>', methods=['GET', 'POST'])
def soh_edit(id):
    from app import db
    from models.soh import SOH
    from models.finished_goods import FinishedGoods
    from models.joining import Joining

    soh = SOH.query.get_or_404(id)

    if request.method == 'POST':
        soh.fg_code = request.form['fg_code']
        soh.description = request.form['description']
        soh.soh_dispatch_boxes = float(request.form['soh_dispatch_boxes']) if request.form.get('soh_dispatch_boxes') else 0.0
        soh.soh_dispatch_units = float(request.form['soh_dispatch_units']) if request.form.get('soh_dispatch_units') else 0.0
        soh.soh_packing_boxes = float(request.form['soh_packing_boxes']) if request.form.get('soh_packing_boxes') else 0.0
        soh.soh_packing_units = float(request.form['soh_packing_units']) if request.form.get('soh_packing_units') else 0.0

        # Fetch units_per_bag from FinishedGoods
        fg = Joining.query.filter_by(fg_code=soh.fg_code).first()
        units_per_bag = fg.units_per_bag if fg and fg.units_per_bag else 1  # Default to 1 if not found

        # Calculate totals
        soh.soh_total_boxes = soh.soh_dispatch_boxes + soh.soh_packing_boxes
        soh.soh_total_units = (
            (soh.soh_dispatch_boxes * units_per_bag) +
            (soh.soh_packing_boxes * units_per_bag) +
            soh.soh_dispatch_units +
            soh.soh_packing_units
        )

        db.session.commit()
        flash("SOH entry updated successfully!", "success")
        return redirect(url_for('soh.soh_list'))

    return render_template('soh/edit.html', soh=soh)

# SOH Delete Route
@soh_bp.route('/soh_delete/<int:id>', methods=['POST'])
def soh_delete(id):
    from app import db
    from models.soh import SOH
    soh = SOH.query.get_or_404(id)

    db.session.delete(soh)
    db.session.commit()
    flash("SOH entry deleted successfully!", "danger")
    return redirect(url_for('soh.soh_list'))

# Autocomplete for SOH FG Code
@soh_bp.route('/autocomplete_soh', methods=['GET'])
def autocomplete_soh():
    from app import db
    from models.joining import Joining  # Import Joining model for autocomplete

    search = request.args.get('query', '').strip()

    if not search:
        return jsonify([])

    try:
        query = text("SELECT fg_code, description FROM joining WHERE fg_code LIKE :search LIMIT 10")
        results = db.session.execute(query, {"search": f"{search}%"}).fetchall()
        suggestions = [{"fg_code": row[0], "description": row[1]} for row in results]
        return jsonify(suggestions)
    except Exception as e:
        print("Error fetching SOH autocomplete suggestions:", e)
        return jsonify([])

# Search SOHs via AJAX
@soh_bp.route('/get_search_sohs', methods=['GET'])
def get_search_sohs():
    from app import db
    from models.soh import SOH

    search_fg_code = request.args.get('fg_code', '').strip()
    search_description = request.args.get('description', '').strip()

    try:
        sohs_query = SOH.query

        if search_fg_code:
            sohs_query = sohs_query.filter(SOH.fg_code.ilike(f"%{search_fg_code}%"))
        if search_description:
            sohs_query = sohs_query.filter(SOH.description.ilike(f"%{search_description}%"))

        sohs = sohs_query.all()

        sohs_data = [
            {
                "id": soh.id,
                "fg_code": soh.fg_code or "",
                "description": soh.description or "",
                "soh_dispatch_boxes": soh.soh_dispatch_boxes if soh.soh_dispatch_boxes is not None else "",
                "soh_dispatch_units": soh.soh_dispatch_units if soh.soh_dispatch_units is not None else "",
                "soh_packing_boxes": soh.soh_packing_boxes if soh.soh_packing_boxes is not None else "",
                "soh_packing_units": soh.soh_packing_units if soh.soh_packing_units is not None else "",
                "soh_total_boxes": soh.soh_total_boxes if soh.soh_total_boxes is not None else "",
                "soh_total_units": soh.soh_total_units if soh.soh_total_units is not None else ""
            }
            for soh in sohs
        ]

        return jsonify(sohs_data)
    except Exception as e:
        print("Error fetching search SOHs:", e)
        return jsonify({"error": "Failed to fetch SOH entries"}), 500