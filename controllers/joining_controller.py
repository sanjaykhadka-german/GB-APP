from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy.sql import text
import sqlalchemy.exc

# Create a Blueprint for joining routes
joining_bp = Blueprint('joining', __name__, template_folder='templates')

# Joining List Route
@joining_bp.route('/joining_list', methods=['GET'])
def joining_list():
    from app import db  # Defer import to runtime
    from models.joining import Joining  # Defer import to runtime

    # Get search parameters from query string
    search_fg_code = request.args.get('fg_code', '').strip()
    search_description = request.args.get('description', '').strip()

    # Query joinings with optional filters
    joinings_query = Joining.query
    if search_fg_code:
        joinings_query = joinings_query.filter(Joining.fg_code.ilike(f"%{search_fg_code}%"))
    if search_description:
        joinings_query = joinings_query.filter(Joining.description.ilike(f"%{search_description}%"))

    joinings = joinings_query.all()

    return render_template('joining/list.html',
                         joinings=joinings,
                         search_fg_code=search_fg_code,
                         search_description=search_description)

# Joining Create Route
@joining_bp.route('/joining_create', methods=['GET', 'POST'])
def joining_create():
    from app import db  # Defer import to runtime
    from models.joining import Joining  # Defer import to runtime
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
    from app import db  # Defer import to runtime
    from models.joining import Joining  # Defer import to runtime
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
    from app import db  # Defer import to runtime
    from models.joining import Joining  # Defer import to runtime
    joining = Joining.query.get(id)

    if joining:
        db.session.delete(joining)
        db.session.commit()
        flash("Joining deleted successfully!", "danger")
    else:
        flash("Joining not found.", "warning")

    return redirect(url_for('joining.joining_list'))

# Autocomplete for Joining FG Code
@joining_bp.route('/autocomplete_joining', methods=['GET'])
def autocomplete_joining():
    from app import db  # Defer import to runtime
    from models.joining import Joining  # Defer import to runtime

    search = request.args.get('query', '').strip()

    if not search:
        return jsonify([])

    try:
        query = text("SELECT fg_code, description FROM joining WHERE fg_code LIKE :search LIMIT 10")
        results = db.session.execute(query, {"search": f"{search}%"}).fetchall()
        suggestions = [{"fg_code": row[0], "description": row[1]} for row in results]
        return jsonify(suggestions)
    except Exception as e:
        print("Error fetching joining autocomplete suggestions:", e)
        return jsonify([])

# Search Joinings via AJAX
@joining_bp.route('/get_search_joinings', methods=['GET'])
def get_search_joinings():
    from app import db  # Defer import to runtime
    from models.joining import Joining  # Defer import to runtime

    search_fg_code = request.args.get('fg_code', '').strip()
    search_description = request.args.get('description', '').strip()

    try:
        joinings_query = Joining.query

        if search_fg_code:
            joinings_query = joinings_query.filter(Joining.fg_code.ilike(f"%{search_fg_code}%"))
        if search_description:
            joinings_query = joinings_query.filter(Joining.description.ilike(f"%{search_description}%"))

        joinings = joinings_query.all()

        joinings_data = [
            {
                "id": joining.id,
                "fg_code": joining.fg_code or "",
                "description": joining.description or "",
                "fw": joining.fw,
                "make_to_order": joining.make_to_order,
                "min_level": joining.min_level if joining.min_level is not None else "",
                "max_level": joining.max_level if joining.max_level is not None else "",
                "kg_per_unit": joining.kg_per_unit if joining.kg_per_unit is not None else "",
                "loss": joining.loss if joining.loss is not None else "",
                "filling_code": joining.filling_code or "",
                "filling_description": joining.filling_description or "",
                "production": joining.production or ""
            }
            for joining in joinings
        ]

        return jsonify(joinings_data)
    except Exception as e:
        print("Error fetching search joinings:", e)
        return jsonify({"error": "Failed to fetch joinings"}), 500