import pandas as pd
import os
from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash
from sqlalchemy.sql import text
from werkzeug.utils import secure_filename
from datetime import datetime, date
import pytz

from controllers.packing_controller import update_packing_entry
from controllers.filling_controller import update_production_entry
from models import joining
from models.packing import Packing


soh_bp = Blueprint('soh', __name__, template_folder='templates')

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@soh_bp.route('/soh_upload', methods=['GET', 'POST'])
def soh_upload():
    from app import db
    from models.soh import SOH
    from models.joining import Joining

    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No file uploaded!", "danger")
            return redirect(request.url)
        
        file = request.files['file']
        sheet_name = request.form.get('sheet_name', '').strip() or 'SOH'

        if file.filename == '':
            flash("No file selected!", "danger")
            return redirect(request.url)
        
        if not file or not allowed_file(file.filename):
            flash("Invalid file type! Only CSV, XLSX, or XLS files are allowed.", "danger")
            return redirect(request.url)

        temp_path = None
        try:
            filename = secure_filename(file.filename)
            temp_path = os.path.join('uploads', filename)
            os.makedirs('uploads', exist_ok=True)
            file.save(temp_path)

            if filename.endswith('.csv'):
                df = pd.read_csv(temp_path)
            else:
                with pd.ExcelFile(temp_path) as excel_file:
                    print("Available sheets:", excel_file.sheet_names)
                    if sheet_name not in excel_file.sheet_names:
                        flash(f"Sheet '{sheet_name}' not found in the Excel file. Available sheets: {', '.join(excel_file.sheet_names)}", "danger")
                        return redirect(request.url)
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)

            df.columns = df.columns.str.strip()

            print("DataFrame columns:", df.columns.tolist())
            print("Full DataFrame content:\n", df.to_string())
            print("DataFrame sample data:", df.head().to_dict())

            required_columns = ['Week Commencing', 'FG Code', 'Description', 'Soh_dispatch_Box', 'Soh_dispatch_Unit', 'Soh_packing_Box', 'Soh_packing_Unit', 'Soh_total_Box', 'Soh_total_Unit']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                flash(f"Missing required columns in file! Missing: {', '.join(missing_columns)}. Expected: {', '.join(required_columns)}", "danger")
                return redirect(request.url)

            numeric_columns = ['Soh_dispatch_Box', 'Soh_dispatch_Unit', 'Soh_packing_Box', 'Soh_packing_Unit', 'Soh_total_Box', 'Soh_total_Unit']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

            for _, row in df.iterrows():
                print("Processing row:", row.to_dict())

                fg_code = str(row['FG Code']).strip()
                description = str(row['Description']).strip() if pd.notnull(row['Description']) else ''

                def safe_float(value):
                    try:
                        if pd.notnull(value) and value != '':
                            return float(value)
                        return 0.0
                    except (ValueError, TypeError) as e:
                        print(f"Error converting value '{value}' to float: {e}")
                        return 0.0

                dispatch_boxes = safe_float(row['Soh_dispatch_Box'])
                dispatch_units = safe_float(row['Soh_dispatch_Unit'])
                packing_boxes = safe_float(row['Soh_packing_Box'])
                packing_units = safe_float(row['Soh_packing_Unit'])
                soh_total_boxes = safe_float(row['Soh_total_Box'])
                soh_total_units = safe_float(row['Soh_total_Unit'])

                # Handle week_commencing
                week_commencing = None
                if pd.notnull(row['Week Commencing']):
                    try:
                        week_commencing = pd.to_datetime(row['Week Commencing']).date()
                    except (ValueError, TypeError) as e:
                        print(f"Error converting Week Commencing '{row['Week Commencing']}' to date: {e}")

                fg = Joining.query.filter_by(fg_code=fg_code).first()
                units_per_bag = fg.units_per_bag if fg and fg.units_per_bag else 1
                print(f"Units per bag for {fg_code}: {units_per_bag}")

                # Recalculate totals to ensure consistency
                soh_total_boxes_calc = dispatch_boxes + packing_boxes
                soh_total_units_calc = (
                    (dispatch_boxes * units_per_bag) +
                    (packing_boxes * units_per_bag) +
                    dispatch_units +
                    packing_units
                )

                print(f"FG Code: {fg_code}, Dispatch Boxes: {dispatch_boxes}, Dispatch Units: {dispatch_units}, "
                      f"Packing Boxes: {packing_boxes}, Packing Units: {packing_units}, "
                      f"Total Boxes: {soh_total_boxes_calc}, Total Units: {soh_total_units_calc}")

                with db.session.no_autoflush:
                    soh = SOH.query.filter_by(fg_code=fg_code, week_commencing=week_commencing).first()
                    if soh:
                        # Check for Packing entries that reference the current SOH
                        packing_entries = Packing.query.filter_by(week_commencing=soh.week_commencing, product_code=fg_code).all()
                        if packing_entries and soh.week_commencing != week_commencing:
                            for packing in packing_entries:
                                packing.week_commencing = week_commencing
                            db.session.commit()

                        soh.description = description
                        soh.soh_dispatch_boxes = dispatch_boxes
                        soh.soh_dispatch_units = dispatch_units
                        soh.soh_packing_boxes = packing_boxes
                        soh.soh_packing_units = packing_units
                        soh.soh_total_boxes = soh_total_boxes_calc
                        soh.soh_total_units = soh_total_units_calc
                        soh.edit_date = datetime.now(pytz.timezone('Australia/Sydney'))
                        print(f"Updating SOH for {fg_code}: {soh.__dict__}")
                    else:
                        new_soh = SOH(
                            week_commencing=week_commencing,
                            fg_code=fg_code,
                            description=description,
                            soh_dispatch_boxes=dispatch_boxes,
                            soh_dispatch_units=dispatch_units,
                            soh_packing_boxes=packing_boxes,
                            soh_packing_units=packing_units,
                            soh_total_boxes=soh_total_boxes_calc,
                            soh_total_units=soh_total_units_calc,
                            edit_date=datetime.now(pytz.timezone('Australia/Sydney'))
                        )
                        db.session.add(new_soh)
                        print(f"Creating new SOH for {fg_code}: {new_soh.__dict__}")

                    # Commit SOH entry before updating Packing
                    db.session.commit()

                    # Update Packing if soh_total_boxes or soh_total_units > 0
                    if soh_total_boxes >= 0 or soh_total_units >= 0:
                        avg_weight_per_unit = fg.kg_per_unit if fg and fg.kg_per_unit else 0.0
                        success, message = update_packing_entry(
                            fg_code=fg_code,
                            description=description,
                            packing_date=date.today(), # packng_date is set to today 
                            special_order_kg=0.0,
                            avg_weight_per_unit=avg_weight_per_unit,
                            soh_requirement_units_week=0,
                            weekly_average=0.0,
                            week_commencing=week_commencing
                        )
                        if success:
                            # update the production entry
                            # update_production_entry(
                            #     packing.packing_date, joining.filling_code, joining)
                            print(f"Updated Packing for {fg_code}: {message}")
                        else:
                            print(f"Failed to update Packing for {fg_code}: {message}")
                            flash(message, "warning")

            flash("SOH data uploaded and updated successfully!", "success")

            saved_soh = SOH.query.filter_by(fg_code='2006.1').first()
            if saved_soh:
                print(f"Saved SOH: FG Code: {saved_soh.fg_code}, Dispatch Boxes: {saved_soh.soh_dispatch_boxes}, "
                      f"Dispatch Units: {saved_soh.soh_dispatch_units}, Packing Boxes: {saved_soh.soh_packing_boxes}, "
                      f"Packing Units: {saved_soh.soh_packing_units}, Total Boxes: {saved_soh.soh_total_boxes}, "
                      f"Total Units: {saved_soh.soh_total_units}")

        except Exception as e:
            db.session.rollback()
            flash(f"Error processing file: {str(e)}", "danger")
            return redirect(request.url)
        
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except PermissionError as e:
                    print(f"Warning: Could not delete temporary file {temp_path}: {e}")

        return redirect(url_for('soh.soh_list'))

    return render_template('soh/upload.html', current_page="soh")

@soh_bp.route('/soh_list', methods=['GET'])
def soh_list():
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
    except Exception as e:
        flash(f"Error fetching SOH list: {str(e)}", "danger")
        sohs = []

    return render_template('soh/list.html',
                           sohs=sohs,
                           SEARCH_FG_CODE=search_fg_code,
                           SEARCH_DESCRIPTION=search_description,
                           current_page="soh")

@soh_bp.route('/soh_create', methods=['GET', 'POST'])
def soh_create():
    from app import db
    from models.soh import SOH
    from models.joining import Joining

    if request.method == 'POST':
        try:
            fg_code = request.form['fg_code'].strip()
            week_commencing = request.form.get('week_commencing')  # Second field
            description = request.form['description'].strip()
            dispatch_boxes = float(request.form.get('soh_dispatch_boxes', 0.0)) if request.form.get('soh_dispatch_boxes') else 0.0
            dispatch_units = float(request.form.get('soh_dispatch_units', 0.0)) if request.form.get('soh_dispatch_units') else 0.0
            packing_boxes = float(request.form.get('soh_packing_boxes', 0.0)) if request.form.get('soh_packing_boxes') else 0.0
            packing_units = float(request.form.get('soh_packing_units', 0.0)) if request.form.get('soh_packing_units') else 0.0

            # Convert week_commencing to date
            week_commencing_date = None
            if week_commencing:
                try:
                    week_commencing_date = datetime.strptime(week_commencing, '%Y-%m-%d').date()
                except ValueError as e:
                    flash(f"Invalid Week Commencing date format: {str(e)}", "danger")
                    return redirect(request.url)

            fg = Joining.query.filter_by(fg_code=fg_code).first()
            units_per_bag = fg.units_per_bag if fg and fg.units_per_bag else 1

            soh_total_boxes = dispatch_boxes + packing_boxes
            soh_total_units = (
                (dispatch_boxes * units_per_bag) +
                (packing_boxes * units_per_bag) +
                dispatch_units +
                packing_units
            )

            new_soh = SOH(
                fg_code=fg_code,
                week_commencing=week_commencing_date,  # Second column
                description=description,
                soh_dispatch_boxes=dispatch_boxes,
                soh_dispatch_units=dispatch_units,
                soh_packing_boxes=packing_boxes,
                soh_packing_units=packing_units,
                soh_total_boxes=soh_total_boxes,
                soh_total_units=soh_total_units,
                edit_date=datetime.now(pytz.timezone('Australia/Sydney'))
            )
            db.session.add(new_soh)
            db.session.commit()

            if soh_total_boxes >= 0 or soh_total_units >= 0:
                avg_weight_per_unit = fg.kg_per_unit if fg and fg.kg_per_unit else 0.0
                success, message = update_packing_entry(
                    fg_code=fg_code,
                    description=description,
                    packing_date=date.today(),
                    special_order_kg=0.0,
                    avg_weight_per_unit=avg_weight_per_unit,
                    soh_requirement_units_week=0,
                    weekly_average=0.0
                )
                if not success:
                    flash(message, "warning")

            flash("SOH entry created successfully!", "success")
            return redirect(url_for('soh.soh_list'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error creating SOH entry: {str(e)}", "danger")
            return redirect(request.url)

    fg_code = request.args.get('fg_code', '')
    return render_template('soh/create.html', fg_code=fg_code, current_page="soh")

@soh_bp.route('/soh_edit/<int:id>', methods=['GET', 'POST'])
def soh_edit(id):
    from app import db
    from models.soh import SOH
    from models.joining import Joining

    soh = SOH.query.get_or_404(id)

    if request.method == 'POST':
        try:
            fg_code = request.form['fg_code'].strip()
            week_commencing = request.form.get('week_commencing')  # Second field
            description = request.form['description'].strip()
            soh_dispatch_boxes = float(request.form.get('soh_dispatch_boxes', 0.0)) if request.form.get('soh_dispatch_boxes') else 0.0
            soh_dispatch_units = float(request.form.get('soh_dispatch_units', 0.0)) if request.form.get('soh_dispatch_units') else 0.0
            soh_packing_boxes = float(request.form.get('soh_packing_boxes', 0.0)) if request.form.get('soh_packing_boxes') else 0.0
            soh_packing_units = float(request.form.get('soh_packing_units', 0.0)) if request.form.get('soh_packing_units') else 0.0

            # Convert week_commencing to date
            week_commencing_date = None
            if week_commencing:
                try:
                    week_commencing_date = datetime.strptime(week_commencing, '%Y-%m-%d').date()
                except ValueError as e:
                    flash(f"Invalid Week Commencing date format: {str(e)}", "danger")
                    return redirect(request.url)

            fg = Joining.query.filter_by(fg_code=fg_code).first()
            units_per_bag = fg.units_per_bag if fg and fg.units_per_bag else 1

            soh_total_boxes = soh_dispatch_boxes + soh_packing_boxes
            soh_total_units = (
                (soh_dispatch_boxes * units_per_bag) +
                (soh_packing_boxes * units_per_bag) +
                soh_dispatch_units +
                soh_packing_units
            )

            soh.fg_code = fg_code
            soh.week_commencing = week_commencing_date  # Second column
            soh.description = description
            soh.soh_dispatch_boxes = soh_dispatch_boxes
            soh.soh_dispatch_units = soh_dispatch_units
            soh.soh_packing_boxes = soh_packing_boxes
            soh.soh_packing_units = soh_packing_units
            soh.soh_total_boxes = soh_total_boxes
            soh.soh_total_units = soh_total_units
            soh.edit_date = datetime.now(pytz.timezone('Australia/Sydney'))

            db.session.commit()

            if soh_total_boxes > 0 or soh_total_units > 0:
                avg_weight_per_unit = fg.kg_per_unit if fg and fg.kg_per_unit else 0.0
                success, message = update_packing_entry(
                    fg_code=fg_code,
                    description=description,
                    packing_date=date.today(),
                    special_order_kg=0.0,
                    avg_weight_per_unit=avg_weight_per_unit,
                    soh_requirement_units_week=0,
                    weekly_average=0.0
                )
                if not success:
                    flash(message, "warning")

            flash("SOH entry updated successfully!", "success")
            return redirect(url_for('soh.soh_list'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error updating SOH entry: {str(e)}", "danger")
            return redirect(request.url)

    return render_template('soh/edit.html', soh=soh, current_page="soh")


@soh_bp.route('/soh_delete/<int:id>', methods=['POST'])
def soh_delete(id):
    from app import db
    from models.soh import SOH

    try:
        soh = SOH.query.get_or_404(id)
        db.session.delete(soh)
        db.session.commit()
        flash("SOH entry deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting SOH entry: {str(e)}", "danger")

    return redirect(url_for('soh.soh_list'))

@soh_bp.route('/autocomplete_soh', methods=['GET'])
def autocomplete_soh():
    from app import db
    from models.joining import Joining

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
                "week_commencing": soh.week_commencing.strftime('%Y-%m-%d') if soh.week_commencing else "",  # Second field
                "fg_code": soh.fg_code or "",
                "description": soh.description or "",
                "soh_dispatch_boxes": soh.soh_dispatch_boxes if soh.soh_dispatch_boxes is not None else "",
                "soh_dispatch_units": soh.soh_dispatch_units if soh.soh_dispatch_units is not None else "",
                "soh_packing_boxes": soh.soh_packing_boxes if soh.soh_packing_boxes is not None else "",
                "soh_packing_units": soh.soh_packing_units if soh.soh_packing_units is not None else "",
                "soh_total_boxes": soh.soh_total_boxes if soh.soh_total_boxes is not None else "",
                "soh_total_units": soh.soh_total_units if soh.soh_total_units is not None else "",
                "edit_date": soh.edit_date.strftime('%Y-%m-%d %H:%M:%S') if soh.edit_date else ""
            }
            for soh in sohs
        ]

        return jsonify(sohs_data)
    except Exception as e:
        print("Error fetching search SOHs:", e)
        return jsonify({"error": "Failed to fetch SOH entries"}), 500