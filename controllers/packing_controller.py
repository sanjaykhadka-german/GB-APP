from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.packing import Packing
from models.production import Production
from models.soh import SOH
from models.filling import Filling
from models.joining import Joining
from datetime import date, datetime, timedelta
from database import db
from sqlalchemy.sql import text
from sqlalchemy import func

packing = Blueprint('packing', __name__, url_prefix='/packing')


def update_packing_entry(fg_code, description, packing_date=None, special_order_kg=0.0, avg_weight_per_unit=0.0, 
                        soh_requirement_units_week=0, weekly_average=0.0, week_commencing=None):
    try:
        packing_date = packing_date or date.today()

        # Use provided week_commencing, or calculate it if not provided
        if week_commencing is None:
            def get_monday_of_week(dt):
                return dt - timedelta(days=dt.weekday())
            week_commencing = get_monday_of_week(packing_date)

        # Check if SOH entry exists for the week_commencing and fg_code
        soh = SOH.query.filter_by(fg_code=fg_code, week_commencing=week_commencing).first()
        if not soh:
            return False, f"No SOH entry found for fg_code {fg_code} and week_commencing {week_commencing}"

        packing = Packing.query.filter_by(product_code=fg_code, packing_date=packing_date).first()
        
        if not packing:
            packing = Packing(
                product_code=fg_code,
                product_description=description,
                packing_date=packing_date,
                week_commencing=week_commencing,  # Use provided or calculated week_commencing
                special_order_kg=special_order_kg,
                avg_weight_per_unit=avg_weight_per_unit,
                soh_requirement_units_week=soh_requirement_units_week,
                weekly_average=weekly_average
            )
            db.session.add(packing)
        else:
            packing.product_description = description
            packing.special_order_kg = special_order_kg
            packing.avg_weight_per_unit = avg_weight_per_unit
            packing.soh_requirement_units_week = soh_requirement_units_week
            packing.weekly_average = weekly_average
            packing.week_commencing = week_commencing  # Update week_commencing

        soh_units = soh.soh_total_units if soh else 0
        avg_weight_per_unit = packing.avg_weight_per_unit if packing.avg_weight_per_unit is not None else 0
        special_order_kg = packing.special_order_kg if packing.special_order_kg is not None else 0
        packing.special_order_unit = int(special_order_kg / avg_weight_per_unit) if avg_weight_per_unit else 0
        packing.soh_kg = round(soh_units * avg_weight_per_unit, 0) if avg_weight_per_unit else 0
        packing.soh_requirement_kg_week = int(packing.soh_requirement_units_week * avg_weight_per_unit) if avg_weight_per_unit and packing.soh_requirement_units_week is not None else 0
        packing.total_stock_kg = packing.soh_requirement_kg_week * packing.weekly_average if packing.weekly_average is not None else 0
        packing.total_stock_units = round(packing.total_stock_kg / avg_weight_per_unit, 0) if avg_weight_per_unit else 0
        packing.requirement_kg = round(packing.total_stock_kg - packing.soh_kg + special_order_kg, 0) if (packing.total_stock_kg - packing.soh_kg + special_order_kg) > 0 else 0
        packing.requirement_unit = packing.total_stock_units - soh_units + packing.special_order_unit if (packing.total_stock_units - soh_units + packing.special_order_unit) > 0 else 0
        packing.avg_weight_per_unit_calc = avg_weight_per_unit
        packing.soh_units = soh_units

        db.session.commit()

        joining = Joining.query.filter_by(fg_code=fg_code).first()
        if joining:
            filling = Filling.query.filter_by(
                filling_date=packing.packing_date,
                fill_code=joining.filling_code
            ).first()

            if filling:
                filling.kilo_per_size = packing.requirement_kg
                filling.description = joining.filling_description
            else:
                filling = Filling(
                    filling_date=packing.packing_date,
                    fill_code=joining.filling_code,
                    description=joining.filling_description,
                    kilo_per_size=packing.requirement_kg,
                    week_commencing=week_commencing  # Set week_commencing
                )
                db.session.add(filling)
            db.session.commit()

            update_production_entry(packing.packing_date, joining.filling_code, joining,week_commencing=week_commencing)  # Pass week_commencing
        else:
            print(f"No Joining record found for product code {fg_code}. Filling entry not updated.")

        return True, "Packing entry updated successfully"
    except Exception as e:
        db.session.rollback()
        print(f"Error updating packing entry for {fg_code}: {str(e)}")
        return False, f"Error updating packing entry: {str(e)}"

@packing.route('/')
def packing_list():
    # Get search parameters from query string
    search_fg_code = request.args.get('fg_code', '').strip()
    search_description = request.args.get('description', '').strip()

    # Query packings with optional filters
    packings_query = Packing.query
    if search_fg_code:
        packings_query = packings_query.filter(Packing.product_code.ilike(f"%{search_fg_code}%"))
    if search_description:
        packings_query = packings_query.filter(Packing.product_description.ilike(f"%{search_description}%"))

    packings = packings_query.all()
    packing_data = []

    # Initialize totals
    total_requirement_kg = 0
    total_requirement_unit = 0

    def get_monday_of_week(dt):
        return dt - timedelta(days=dt.weekday())

    for packing in packings:
        # Calculate week_commencing for the packing_date
        week_commencing = get_monday_of_week(packing.packing_date)

        # Fetch SOH units (L2) from SOH model for the specific week
        soh = SOH.query.filter_by(fg_code=packing.product_code, week_commencing=week_commencing).first()
        soh_units = soh.soh_total_units if soh else 0  # L2

        # Calculations based on Excel formulas
        avg_weight_per_unit = packing.avg_weight_per_unit if packing.avg_weight_per_unit is not None else 0  # H2, M2
        special_order_kg = packing.special_order_kg if packing.special_order_kg is not None else 0  # D2
        special_order_unit = int(special_order_kg / avg_weight_per_unit) if avg_weight_per_unit else 0  # E2
        soh_kg = round(soh_units * avg_weight_per_unit, 0) if avg_weight_per_unit else 0  # K2
        soh_requirement_kg_week = int(packing.soh_requirement_units_week * avg_weight_per_unit) if avg_weight_per_unit and packing.soh_requirement_units_week is not None else 0  # I2
        total_stock_kg = soh_requirement_kg_week * packing.weekly_average if packing.weekly_average is not None else 0  # N2
        total_stock_units = round(total_stock_kg / avg_weight_per_unit, 0) if avg_weight_per_unit else 0  # O2
        requirement_kg = round(total_stock_kg - soh_kg + special_order_kg, 0) if (total_stock_kg - soh_kg + special_order_kg) > 0 else 0  # F2
        requirement_unit = total_stock_units - soh_units + special_order_unit if (total_stock_units - soh_units + special_order_unit) > 0 else 0  # G2

        # Accumulate totals
        total_requirement_kg += requirement_kg
        total_requirement_unit += requirement_unit

        packing_data.append({
            'packing': packing,
            'special_order_unit': special_order_unit,
            'requirement_kg': requirement_kg,
            'requirement_unit': requirement_unit,
            'soh_requirement_kg_week': soh_requirement_kg_week,
            'soh_kg': soh_kg,
            'soh_units': soh_units,
            'total_stock_kg': total_stock_kg,
            'total_stock_units': total_stock_units,
            'week_commencing': week_commencing.strftime('%Y-%m-%d') if week_commencing else ''  # Add week_commencing
        })

    return render_template('packing/list.html',
                         packing_data=packing_data,
                         search_fg_code=search_fg_code,
                         search_description=search_description,
                         total_requirement_kg=total_requirement_kg,
                         total_requirement_unit=total_requirement_unit,
                         current_page="packing")

@packing.route('/create', methods=['GET', 'POST'])
def packing_create():
    if request.method == 'POST':
        try:
            packing_date = datetime.strptime(request.form['packing_date'], '%Y-%m-%d').date()
            product_code = request.form['product_code']
            product_description = request.form['product_description']
            special_order_kg = float(request.form['special_order_kg']) if request.form['special_order_kg'] else 0.0
            avg_weight_per_unit = float(request.form['avg_weight_per_unit']) if request.form['avg_weight_per_unit'] else 0.0
            soh_requirement_units_week = int(request.form['soh_requirement_units_week']) if request.form['soh_requirement_units_week'] else 0
            weekly_average = float(request.form['weekly_average']) if request.form['weekly_average'] else 0.0

            # Calculate week_commencing for the packing_date
            def get_monday_of_week(dt):
                return dt - timedelta(days=dt.weekday())
            week_commencing = get_monday_of_week(packing_date)

            # Fetch SOH data for the specific week
            soh = SOH.query.filter_by(fg_code=product_code, week_commencing=week_commencing).first()
            soh_units = soh.soh_total_units if soh else 0  # L2

            # Calculations based on Excel formulas
            special_order_unit = int(special_order_kg / avg_weight_per_unit) if avg_weight_per_unit else 0  # E2
            soh_kg = round(soh_units * avg_weight_per_unit, 0) if avg_weight_per_unit else 0  # K2
            soh_requirement_kg_week = int(soh_requirement_units_week * avg_weight_per_unit) if avg_weight_per_unit else 0  # I2
            total_stock_kg = soh_requirement_kg_week * weekly_average if weekly_average is not None else 0  # N2
            total_stock_units = round(total_stock_kg / avg_weight_per_unit, 0) if avg_weight_per_unit else 0  # O2
            requirement_kg = round(total_stock_kg - soh_kg + special_order_kg, 0) if (total_stock_kg - soh_kg + special_order_kg) > 0 else 0  # F2
            requirement_unit = total_stock_units - soh_units + special_order_unit if (total_stock_units - soh_units + special_order_unit) > 0 else 0  # G2

            new_packing = Packing(
                packing_date=packing_date,
                product_code=product_code,
                product_description=product_description,
                special_order_kg=special_order_kg,
                special_order_unit=special_order_unit,
                requirement_kg=requirement_kg,
                requirement_unit=requirement_unit,
                avg_weight_per_unit=avg_weight_per_unit,
                avg_weight_per_unit_calc=avg_weight_per_unit,
                soh_requirement_kg_week=soh_requirement_kg_week,
                soh_requirement_units_week=soh_requirement_units_week,
                soh_kg=soh_kg,
                soh_units=soh_units,
                total_stock_kg=total_stock_kg,
                total_stock_units=total_stock_units,
                weekly_average=weekly_average,
                week_commencing=week_commencing  # Ensure Packing has week_commencing
            )
            db.session.add(new_packing)
            db.session.commit()

            # Create or update corresponding Filling entry
            joining = Joining.query.filter_by(fg_code=product_code).first()
            if joining:
                existing_filling = Filling.query.filter_by(
                    filling_date=packing_date,
                    fill_code=joining.filling_code
                ).first()

                if existing_filling:
                    existing_filling.kilo_per_size += requirement_kg
                    existing_filling.description = joining.filling_description
                    existing_filling.week_commencing = week_commencing  # Set week_commencing
                else:
                    new_filling = Filling(
                        filling_date=packing_date,
                        fill_code=joining.filling_code,
                        description=joining.filling_description,
                        kilo_per_size=requirement_kg,
                        week_commencing=week_commencing  # Set week_commencing
                    )
                    db.session.add(new_filling)
                db.session.commit()

                update_production_entry(packing_date, joining.filling_code, joining, week_commencing)  # Pass week_commencing
            else:
                flash(f"No Joining record found for product code {product_code}. Filling entry not created.", 'warning')

            flash('Packing entry created successfully!', 'success')
            return redirect(url_for('packing.packing_list'))
        except ValueError as e:
            db.session.rollback()
            flash(f'Invalid data format: {str(e)}', 'danger')
        except KeyError as e:
            db.session.rollback()
            flash(f'Missing required field: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating packing entry: {str(e)}', 'danger')

    # Fetch product codes for dropdown, including week_commencing
    products = SOH.query.order_by(SOH.week_commencing.desc(), SOH.fg_code).all()
    return render_template('packing/create.html', products=products, current_page="packing")

@packing.route('/edit/<int:id>', methods=['GET', 'POST'])
def packing_edit(id):
    packing = Packing.query.get_or_404(id)

    if request.method == 'POST':
        try:
            packing.packing_date = datetime.strptime(request.form['packing_date'], '%Y-%m-%d').date()
            packing.product_code = request.form['product_code']
            packing.product_description = request.form['product_description']
            packing.special_order_kg = float(request.form['special_order_kg']) if request.form['special_order_kg'] else 0.0
            packing.avg_weight_per_unit = float(request.form['avg_weight_per_unit']) if request.form['avg_weight_per_unit'] else 0.0
            packing.soh_requirement_units_week = int(request.form['soh_requirement_units_week']) if request.form['soh_requirement_units_week'] else 0
            packing.weekly_average = float(request.form['weekly_average']) if request.form['weekly_average'] else 0.0
            # Handle week_commencing from form
            week_commencing = datetime.strptime(request.form['week_commencing'], '%Y-%m-%d').date() if request.form['week_commencing'] else None

            # If week_commencing is not provided, calculate it
            if not week_commencing:
                def get_monday_of_week(dt):
                    return dt - timedelta(days=dt.weekday())
                week_commencing = get_monday_of_week(packing.packing_date)

            # Fetch SOH data for the specific week
            soh = SOH.query.filter_by(fg_code=packing.product_code, week_commencing=week_commencing).first()
            soh_units = soh.soh_total_units if soh else 0  # L2

            # Calculations based on Excel formulas
            avg_weight_per_unit = packing.avg_weight_per_unit if packing.avg_weight_per_unit is not None else 0
            special_order_kg = packing.special_order_kg if packing.special_order_kg is not None else 0
            packing.special_order_unit = int(special_order_kg / avg_weight_per_unit) if avg_weight_per_unit else 0  # E2
            packing.soh_kg = round(soh_units * avg_weight_per_unit, 0) if avg_weight_per_unit else 0  # K2
            packing.soh_requirement_kg_week = int(packing.soh_requirement_units_week * avg_weight_per_unit) if avg_weight_per_unit and packing.soh_requirement_units_week is not None else 0  # I2
            packing.total_stock_kg = packing.soh_requirement_kg_week * packing.weekly_average if packing.weekly_average is not None else 0  # N2
            packing.total_stock_units = round(packing.total_stock_kg / avg_weight_per_unit, 0) if avg_weight_per_unit else 0  # O2
            packing.requirement_kg = round(packing.total_stock_kg - packing.soh_kg + special_order_kg, 0) if (packing.total_stock_kg - packing.soh_kg + special_order_kg) > 0 else 0  # F2
            packing.requirement_unit = packing.total_stock_units - soh_units + packing.special_order_unit if (packing.total_stock_units - soh_units + packing.special_order_unit) > 0 else 0  # G2
            packing.avg_weight_per_unit_calc = avg_weight_per_unit  # M2 = H2
            packing.soh_units = soh_units  # L2
            packing.week_commencing = week_commencing  # Update week_commencing

            db.session.commit()

            # Update or create corresponding Filling entry
            joining = Joining.query.filter_by(fg_code=packing.product_code).first()
            if joining:
                filling = Filling.query.filter_by(
                    filling_date=packing.packing_date,
                    fill_code=joining.filling_code
                ).first()

                if filling:
                    filling.kilo_per_size += packing.requirement_kg  # Use = instead of += to avoid double-counting
                    filling.description = joining.filling_description
                    filling.week_commencing = week_commencing  # Set week_commencing
                else:
                    filling = Filling(
                        filling_date=packing.packing_date,
                        fill_code=joining.filling_code,
                        description=joining.filling_description,
                        kilo_per_size=packing.requirement_kg,
                        week_commencing=week_commencing  # Set week_commencing
                    )
                    db.session.add(filling)
                db.session.commit()

                update_production_entry(packing.packing_date, joining.filling_code, joining, week_commencing)
            else:
                flash(f"No Joining record found for product code {packing.product_code}. Filling entry not updated.", 'warning')

            flash('Packing entry updated successfully!', 'success')
            return redirect(url_for('packing.packing_list'))
        except ValueError as e:
            db.session.rollback()
            flash(f'Invalid data format: {str(e)}', 'danger')
        except KeyError as e:
            db.session.rollback()
            flash(f'Missing required field: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating packing entry: {str(e)}', 'danger')

    # Fetch product codes for dropdown
    products = SOH.query.order_by(SOH.week_commencing.desc(), SOH.fg_code).all()

    # Fetch production entries
    productions = Production.query.order_by(Production.production_date.desc()).all()
    
    # Calculate total_kg sum
    total_production_kg = sum(production.total_kg for production in productions if production.total_kg is not None)

    return render_template('packing/edit.html', 
                         packing=packing, 
                         products=products, 
                         productions=productions, 
                         total_production_kg=total_production_kg, 
                         current_page="packing")


@packing.route('/delete/<int:id>', methods=['POST'])
def packing_delete(id):
    packing = Packing.query.get_or_404(id)
    try:
        # Adjust corresponding Filling entry
        joining = Joining.query.filter_by(fg_code=packing.product_code).first()
        if joining:
            filling = Filling.query.filter_by(
                filling_date=packing.packing_date,
                fill_code=joining.filling_code
            ).first()
            if filling:
                filling.kilo_per_size -= packing.requirement_kg
                if filling.kilo_per_size <= 0:
                    db.session.delete(filling)
                else:
                    db.session.commit()
                # Update corresponding Production entry
                update_production_entry(packing.packing_date, joining.filling_code, joining, packing.week_commencing)  # Pass week_commencing

        db.session.delete(packing)
        db.session.commit()
        flash('Packing entry deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting packing entry: {str(e)}', 'danger')
    return redirect(url_for('packing.packing_list'))

# Autocomplete for Packing Product Code
@packing.route('/autocomplete_packing', methods=['GET'])
def autocomplete_packing():
    search = request.args.get('query', '').strip()

    if not search:
        return jsonify([])

    try:
        query = text("SELECT fg_code, description FROM joining WHERE fg_code LIKE :search LIMIT 10")
        results = db.session.execute(query, {"search": f"{search}%"}).fetchall()
        suggestions = [{"fg_code": row[0], "description": row[1]} for row in results]
        return jsonify(suggestions)
    except Exception as e:
        print("Error fetching packing autocomplete suggestions:", e)
        return jsonify([])

@packing.route('/get_search_packings', methods=['GET'])
def get_search_packings():
    search_fg_code = request.args.get('fg_code', '').strip()
    search_description = request.args.get('description', '').strip()

    try:
        packings_query = Packing.query

        if search_fg_code:
            packings_query = packings_query.filter(Packing.product_code.ilike(f"%{search_fg_code}%"))
        if search_description:
            packings_query = packings_query.filter(Packing.product_description.ilike(f"%{search_description}%"))

        packings = packings_query.all()
        packing_data = []

        def get_monday_of_week(dt):
            return dt - timedelta(days=dt.weekday())

        for packing in packings:
            # Calculate week_commencing for the packing_date
            week_commencing = get_monday_of_week(packing.packing_date)

            # Fetch SOH units (L2) from SOH model for the specific week
            soh = SOH.query.filter_by(fg_code=packing.product_code, week_commencing=week_commencing).first()
            soh_units = soh.soh_total_units if soh else 0  # L2

            # Calculations based on Excel formulas
            avg_weight_per_unit = packing.avg_weight_per_unit if packing.avg_weight_per_unit is not None else 0  # H2, M2
            special_order_kg = packing.special_order_kg if packing.special_order_kg is not None else 0  # D2
            special_order_unit = int(special_order_kg / avg_weight_per_unit) if avg_weight_per_unit else 0  # E2
            soh_kg = round(soh_units * avg_weight_per_unit, 0) if avg_weight_per_unit else 0  # K2
            soh_requirement_kg_week = int(packing.soh_requirement_units_week * avg_weight_per_unit) if avg_weight_per_unit and packing.soh_requirement_units_week is not None else 0  # I2
            total_stock_kg = soh_requirement_kg_week * packing.weekly_average if packing.weekly_average is not None else 0  # N2
            total_stock_units = round(total_stock_kg / avg_weight_per_unit, 0) if avg_weight_per_unit else 0  # O2
            requirement_kg = round(total_stock_kg - soh_kg + special_order_kg, 0) if (total_stock_kg - soh_kg + special_order_kg) > 0 else 0  # F2
            requirement_unit = total_stock_units - soh_units + special_order_unit if (total_stock_units - soh_units + special_order_unit) > 0 else 0  # G2

            packing_data.append({
                "id": packing.id,
                "packing_date": packing.packing_date.strftime('%Y-%m-%d') if packing.packing_date else "",
                "week_commencing": week_commencing.strftime('%Y-%m-%d') if week_commencing else "",  # Add week_commencing
                "product_code": packing.product_code or "",
                "product_description": packing.product_description or "",
                "special_order_kg": packing.special_order_kg if packing.special_order_kg is not None else "",
                "special_order_unit": special_order_unit,
                "requirement_kg": requirement_kg,
                "requirement_unit": requirement_unit,
                "avg_weight_per_unit": packing.avg_weight_per_unit if packing.avg_weight_per_unit is not None else "",
                "soh_requirement_kg_week": soh_requirement_kg_week,
                "soh_requirement_units_week": packing.soh_requirement_units_week if packing.soh_requirement_units_week is not None else "",
                "soh_kg": soh_kg,
                "soh_units": soh_units,
                "avg_weight_per_unit_calc": packing.avg_weight_per_unit_calc if packing.avg_weight_per_unit_calc is not None else "",
                "total_stock_kg": total_stock_kg,
                "total_stock_units": total_stock_units,
                "weekly_average": packing.weekly_average if packing.weekly_average is not None else ""
            })

        return jsonify(packing_data)
    except Exception as e:
        print("Error fetching search packings:", e)
        return jsonify({"error": "Failed to fetch packing entries"}), 500

def update_production_entry(filling_date, fill_code, joining, week_commencing=None):
    """Helper function to create or update a Production entry."""
    try:
        # Get production_code and description from Joining
        production_code = joining.production
        description = joining.description

        fill_code_prefix = fill_code.split('.')[0] if '.' in fill_code else fill_code
        if len(fill_code_prefix) > 1:
            # Aggregate total_kg for all Filling entries with the same filling_date and fill_code prefix
            total_kg = db.session.query(func.sum(Filling.kilo_per_size)).filter(
                Filling.filling_date == filling_date,
                func.substring_index(Filling.fill_code, '.', 1) == fill_code_prefix
            ).scalar() or 0.0
        else:
            # Aggregate total_kg for Filling entries with matching fill_code and filling_date
            total_kg = db.session.query(func.sum(Filling.kilo_per_size)).filter(
                Filling.filling_date == filling_date,
                Filling.fill_code == fill_code
            ).scalar() or 0.0

        # If total_kg is 0, delete the Production entry if it exists
        if total_kg == 0.0:
            production = Production.query.filter_by(
                production_date=filling_date,
                production_code=production_code
            ).first()
            if production:
                db.session.delete(production)
                db.session.commit()
            return

        # Calculate batches
        batches = total_kg / 300 if total_kg > 0 else 0.0

        # Check for existing Production entry
        production = Production.query.filter_by(
            production_date=filling_date,
            production_code=production_code
        ).first()

        if production:
            # Update existing Production entry
            production.description = description
            production.total_kg = total_kg
            production.batches = batches
            production.week_commencing = week_commencing  # Set week_commencing
        else:
            # Create new Production entry
            production = Production(
                production_date=filling_date,
                production_code=production_code,
                description=description,
                batches=batches,
                total_kg=total_kg,
                week_commencing=week_commencing  # Set week_commencing
            )
            db.session.add(production)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating Production entry: {str(e)}", 'error')