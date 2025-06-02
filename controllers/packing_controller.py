from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from models.machinery import Machinery
from models.packing import Packing
from models.production import Production
from models.soh import SOH
from models.filling import Filling
from models.joining import Joining
from datetime import date, datetime, timedelta
from database import db
from sqlalchemy.sql import text
from sqlalchemy import asc, desc, func
import pandas as pd
import io
import logging

#set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

packing = Blueprint('packing', __name__, url_prefix='/packing')


def update_packing_entry(fg_code, description, packing_date=None, special_order_kg=0.0, avg_weight_per_unit=None, 
                        soh_requirement_units_week=0, weekly_average=0.0, week_commencing=None, machinery=None):
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

        # Fetch avg_weight_per_unit from Joining table
        joining = Joining.query.filter_by(fg_code=fg_code).first()
        if not joining:
            return False, f"No Joining entry found for fg_code {fg_code}"
        avg_weight_per_unit = joining.kg_per_unit or 0.0  # Fetch from Joining

        # Calculate soh_requirement_units_week based on SOH and Joining
        soh_units = soh.soh_total_units if soh else 0
        min_level = joining.min_level or 0.0
        max_level = joining.max_level or 0.0
        if soh_units < min_level:
            soh_requirement_units_week = int(max_level - soh_units)
        else:
            soh_requirement_units_week = 0

        packing = Packing.query.filter_by(product_code=fg_code, packing_date=packing_date).first()
        
        if not packing:
            packing = Packing(
                product_code=fg_code,
                product_description=description,
                packing_date=packing_date,
                week_commencing=week_commencing,  
                special_order_kg=special_order_kg,
                avg_weight_per_unit=avg_weight_per_unit,
                soh_requirement_units_week=soh_requirement_units_week,
                weekly_average=weekly_average,
                machinery=machinery  # Set machinery
            )
            db.session.add(packing)
        else:
            packing.product_description = description
            packing.special_order_kg = special_order_kg
            packing.avg_weight_per_unit = avg_weight_per_unit
            packing.soh_requirement_units_week = soh_requirement_units_week
            packing.weekly_average = weekly_average
            packing.week_commencing = week_commencing
            packing.machinery = machinery  # Update machinery

        # Perform calculations
        special_order_kg = packing.special_order_kg if packing.special_order_kg is not None else 0
        packing.special_order_unit = int(special_order_kg / avg_weight_per_unit) if avg_weight_per_unit else 0
        packing.soh_kg = round(soh_units * avg_weight_per_unit, 0) if avg_weight_per_unit else 0
        packing.soh_requirement_kg_week = int(packing.soh_requirement_units_week * avg_weight_per_unit) if avg_weight_per_unit else 0
        packing.total_stock_kg = packing.soh_requirement_kg_week * packing.weekly_average if packing.weekly_average is not None else 0
        packing.total_stock_units = round(packing.total_stock_kg / avg_weight_per_unit, 0) if avg_weight_per_unit else 0
        packing.requirement_kg = round(packing.total_stock_kg - packing.soh_kg + special_order_kg, 0) if (packing.total_stock_kg - packing.soh_kg + special_order_kg) > 0 else 0
        packing.requirement_unit = packing.total_stock_units - soh_units + packing.special_order_unit if (packing.total_stock_units - soh_units + packing.special_order_unit) > 0 else 0
        packing.soh_units = soh_units

        db.session.commit()

        # Update Filling and Production entries (unchanged)
        joining = Joining.query.filter_by(fg_code=fg_code).first()
        if joining:
            filling = Filling.query.filter_by(
                filling_date=packing.packing_date,
                fill_code=joining.filling_code
            ).first()

            if filling:
                filling.kilo_per_size = packing.requirement_kg
                filling.description = joining.filling_description
                filling.week_commencing = week_commencing
            else:
                filling = Filling(
                    filling_date=packing.packing_date,
                    fill_code=joining.filling_code,
                    description=joining.filling_description,
                    kilo_per_size=packing.requirement_kg,
                    week_commencing=week_commencing
                )
                db.session.add(filling)
            db.session.commit()

            update_production_entry(packing.packing_date, joining.filling_code, joining, week_commencing=week_commencing)
        else:
            logger.warning(f"No Joining record found for product code {fg_code}. Filling entry not updated.")

        return True, "Packing entry updated successfully"
    except Exception as e:
        db.session.rollback()
        logger.warning(f"Error updating packing entry for {fg_code}: {str(e)}")
        return False, f"Error updating packing entry: {str(e)}"

@packing.route('/')
def packing_list():
    search_fg_code = request.args.get('fg_code', '').strip()
    search_description = request.args.get('description', '').strip()
    search_week_commencing = request.args.get('week_commencing', '').strip()

    packings_query = Packing.query
    if search_fg_code:
        packings_query = packings_query.filter(Packing.product_code.ilike(f"%{search_fg_code}%"))
    if search_description:
        packings_query = packings_query.filter(Packing.product_description.ilike(f"%{search_description}%"))
    if search_week_commencing:
        try:
            week_commencing_date = datetime.strptime(search_week_commencing, '%Y-%m-%d').date()
            packings_query = packings_query.filter(Packing.week_commencing == week_commencing_date)
        except ValueError:
            flash('Invalid date format for week commencing. Please use YYYY-MM-DD.', 'danger')

    packings = packings_query.all()
    packing_data = []
    total_requirement_kg = 0
    total_requirement_unit = 0

    def get_monday_of_week(dt):
        return dt - timedelta(days=dt.weekday())

    for packing in packings:
        week_commencing = packing.week_commencing or get_monday_of_week(packing.packing_date)
        soh = SOH.query.filter_by(fg_code=packing.product_code, week_commencing=week_commencing).first()
        soh_units = soh.soh_total_units if soh else 0
        joining = Joining.query.filter_by(fg_code=packing.product_code).first()
        avg_weight_per_unit = joining.kg_per_unit if joining else 0.0
        min_level = joining.min_level or 0.0 if joining else 0.0
        max_level = joining.max_level or 0.0 if joining else 0.0
        soh_requirement_units_week = int(max_level - soh_units) if soh_units < min_level else 0

        special_order_kg = packing.special_order_kg if packing.special_order_kg is not None else 0
        special_order_unit = int(special_order_kg / avg_weight_per_unit) if avg_weight_per_unit else 0
        soh_kg = round(soh_units * avg_weight_per_unit, 0) if avg_weight_per_unit else 0
        soh_requirement_kg_week = int(soh_requirement_units_week * avg_weight_per_unit) if avg_weight_per_unit else 0
        total_stock_kg = soh_requirement_kg_week * packing.weekly_average if packing.weekly_average is not None else 0
        total_stock_units = round(total_stock_kg / avg_weight_per_unit, 0) if avg_weight_per_unit else 0
        requirement_kg = round(total_stock_kg - soh_kg + special_order_kg, 0) if (total_stock_kg - soh_kg + special_order_kg) > 0 else 0
        requirement_unit = total_stock_units - soh_units + special_order_unit if (total_stock_units - soh_units + special_order_unit) > 0 else 0

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
            'week_commencing': week_commencing.strftime('%Y-%m-%d') if week_commencing else '',
            'machinery': packing.machinery,
            'priority': packing.priority
        })

    return render_template('packing/list.html',
                         search_week_commencing=search_week_commencing,
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
            weekly_average = float(request.form['weekly_average']) if request.form['weekly_average'] else 0.0
            week_commencing = datetime.strptime(request.form['week_commencing'], '%Y-%m-%d').date() if request.form['week_commencing'] else None
            machinery = int(request.form['machinery']) if request.form['machinery'] else None
            priority = int(request.form['priority']) if request.form['priority'] else 0

            # Calculate week_commencing
            if not week_commencing:
                def get_monday_of_week(dt):
                    return dt - timedelta(days=dt.weekday())
                week_commencing = get_monday_of_week(packing_date)

            # Fetch Joining data for avg_weight_per_unit
            joining = Joining.query.filter_by(fg_code=product_code).first()
            if not joining:
                flash(f"No Joining record found for product code {product_code}.", 'danger')
                return redirect(url_for('packing.packing_create'))
            avg_weight_per_unit = joining.kg_per_unit or 0.0

            # Fetch SOH data and calculate soh_requirement_units_week
            soh = SOH.query.filter_by(fg_code=product_code, week_commencing=week_commencing).first()
            soh_units = soh.soh_total_units if soh else 0
            min_level = joining.min_level or 0.0
            max_level = joining.max_level or 0.0
            soh_requirement_units_week = int(max_level - soh_units) if soh_units < min_level else 0

            # Perform calculations
            special_order_unit = int(special_order_kg / avg_weight_per_unit) if avg_weight_per_unit else 0
            soh_kg = round(soh_units * avg_weight_per_unit, 0) if avg_weight_per_unit else 0
            soh_requirement_kg_week = int(soh_requirement_units_week * avg_weight_per_unit) if avg_weight_per_unit else 0
            total_stock_kg = soh_requirement_kg_week * weekly_average if weekly_average is not None else 0
            total_stock_units = round(total_stock_kg / avg_weight_per_unit, 0) if avg_weight_per_unit else 0
            requirement_kg = round(total_stock_kg - soh_kg + special_order_kg, 0) if (total_stock_kg - soh_kg + special_order_kg) > 0 else 0
            requirement_unit = total_stock_units - soh_units + special_order_unit if (total_stock_units - soh_units + special_order_unit) > 0 else 0

            new_packing = Packing(
                packing_date=packing_date,
                product_code=product_code,
                product_description=product_description,
                special_order_kg=special_order_kg,
                special_order_unit=special_order_unit,
                requirement_kg=requirement_kg,
                requirement_unit=requirement_unit,
                avg_weight_per_unit=avg_weight_per_unit,
                soh_requirement_kg_week=soh_requirement_kg_week,
                soh_requirement_units_week=soh_requirement_units_week,
                soh_kg=soh_kg,
                soh_units=soh_units,
                total_stock_kg=total_stock_kg,
                total_stock_units=total_stock_units,
                weekly_average=weekly_average,
                week_commencing=week_commencing,
                machinery=machinery,
                priority=priority
            )
            db.session.add(new_packing)
            db.session.commit()

            # Update Filling and Production (unchanged)
            if joining:
                existing_filling = Filling.query.filter_by(
                    filling_date=packing_date,
                    fill_code=joining.filling_code
                ).first()

                if existing_filling:
                    existing_filling.kilo_per_size += requirement_kg
                    existing_filling.description = joining.filling_description
                    existing_filling.week_commencing = week_commencing
                else:
                    new_filling = Filling(
                        filling_date=packing_date,
                        fill_code=joining.filling_code,
                        description=joining.filling_description,
                        kilo_per_size=requirement_kg,
                        week_commencing=week_commencing
                    )
                    db.session.add(new_filling)
                db.session.commit()

                update_production_entry(packing_date, joining.filling_code, joining, week_commencing)
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

    # Fetch machinery and products for dropdowns
    products = SOH.query.order_by(SOH.week_commencing.desc(), SOH.fg_code).all()
    machinery = Machinery.query.all()
    return render_template('packing/create.html', products=products, machinery=machinery, current_page="packing")

@packing.route('/edit/<int:id>', methods=['GET', 'POST'])
def packing_edit(id):
    packing = Packing.query.get_or_404(id)

    if request.method == 'POST':
        try:
            original_requirement_kg = packing.requirement_kg or 0.0

            packing.packing_date = datetime.strptime(request.form['packing_date'], '%Y-%m-%d').date()
            packing.product_code = request.form['product_code']
            packing.product_description = request.form['product_description']
            packing.special_order_kg = float(request.form['special_order_kg']) if request.form['special_order_kg'] else 0.0
            packing.weekly_average = float(request.form['weekly_average']) if request.form['weekly_average'] else 0.0
            #packing.machinery = int(request.form.get('machinery')) if request.form.get('machinery') and request.form['machinery'].strip() else None
            machinery_value = request.form.get('machinery')
            if machinery_value and machinery_value.strip():
                packing.machinery = int(machinery_value)
            else:
                packing.machinery = None
            packing.priority = int(request.form['priority']) if request.form['priority'] else 0
            week_commencing = datetime.strptime(request.form['week_commencing'], '%Y-%m-%d').date() if request.form['week_commencing'] else None

            if not week_commencing:
                def get_monday_of_week(dt):
                    return dt - timedelta(days=dt.weekday())
                week_commencing = get_monday_of_week(packing.packing_date)
            
            # Validate machinery
            if packing.machinery is not None:
                machinery_exists = Machinery.query.filter_by(machineID=packing.machinery).first()
                if not machinery_exists:
                    flash(f'Invalid machinery ID {packing.machinery}. Please select a valid machinery.', 'danger')
                    return redirect(url_for('packing.packing_edit', id=id))

            # Fetch avg_weight_per_unit from Joining
            joining = Joining.query.filter_by(fg_code=packing.product_code).first()
            if not joining:
                flash(f"No Joining record found for {packing.product_code}.", 'danger')
                return redirect(url_for('packing.packing_edit', id=id))
            avg_weight_per_unit = joining.kg_per_unit or 0.0
            packing.avg_weight_per_unit = avg_weight_per_unit

            # Calculate soh_requirement_units_week
            soh = SOH.query.filter_by(fg_code=packing.product_code, week_commencing=week_commencing).first()
            soh_units = soh.soh_total_units if soh else 0
            min_level = joining.min_level or 0.0
            max_level = joining.max_level or 0.0
            packing.soh_requirement_units_week = int(max_level - soh_units) if soh_units < min_level else 0

            # Recalculate fields
            special_order_kg = packing.special_order_kg if packing.special_order_kg is not None else 0
            packing.special_order_unit = int(special_order_kg / avg_weight_per_unit) if avg_weight_per_unit else 0
            packing.soh_kg = round(soh_units * avg_weight_per_unit, 0) if avg_weight_per_unit else 0
            packing.soh_requirement_kg_week = int(packing.soh_requirement_units_week * avg_weight_per_unit) if avg_weight_per_unit else 0
            packing.total_stock_kg = packing.soh_requirement_kg_week * packing.weekly_average if packing.weekly_average is not None else 0
            packing.total_stock_units = round(packing.total_stock_kg / avg_weight_per_unit, 0) if avg_weight_per_unit else 0
            packing.requirement_kg = round(packing.total_stock_kg - packing.soh_kg + special_order_kg, 0) if (packing.total_stock_kg - packing.soh_kg + special_order_kg) > 0 else 0
            packing.requirement_unit = packing.total_stock_units - soh_units + packing.special_order_unit if (packing.total_stock_units - soh_units + packing.special_order_unit) > 0 else 0
            packing.soh_units = soh_units
            packing.week_commencing = week_commencing

            # new_requirement_kg = packing.requirement_kg or 0.0
            # delta_kg = new_requirement_kg - original_requirement_kg

             # Aggregate delta_kg for all related packings
            recipe_code_prefix = packing.product_code.split('.')[0]
            related_packings = Packing.query.filter(
                Packing.week_commencing == packing.week_commencing,
                Packing.product_code.ilike(f"{recipe_code_prefix}%")
            ).all()
            total_new_requirement_kg = sum(p.requirement_kg or 0.0 for p in related_packings)
            original_total_requirement_kg = sum(p.requirement_kg or 0.0 for p in related_packings if p.id != id) + original_requirement_kg
            delta_kg = total_new_requirement_kg - original_total_requirement_kg

            db.session.commit()

            # Update Filling and Production (unchanged)
            if joining:
                filling = Filling.query.filter_by(
                    filling_date=packing.packing_date,
                    fill_code=joining.filling_code,
                    week_commencing=packing.week_commencing
                ).first()

                if filling:
                    filling.kilo_per_size = (filling.kilo_per_size or 0.0) + delta_kg
                    # filling.description = joining.filling_description
                    # filling.week_commencing = week_commencing
                    if filling.kilo_per_size <= 0:
                        db.session.delete(filling)
                else:
                    if delta_kg > 0:
                        filling = Filling(
                            filling_date=packing.packing_date,
                            fill_code=joining.filling_code,
                            description=joining.filling_description,
                            kilo_per_size=delta_kg,
                            week_commencing=packing.week_commencing
                        )
                        db.session.add(filling)
                db.session.commit()

                update_production_entry(packing.packing_date, joining.filling_code, joining, packing.week_commencing)
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

    # Fetch machinery, products, and related data
    products = SOH.query.order_by(SOH.week_commencing.desc(), SOH.fg_code).all()
    machinery = Machinery.query.all()
    
    logger.debug(f"Machinery records: {[m.__dict__ for m in machinery]}")
    logger.debug(f"Packing machinery: {packing.machinery}")

    machinery_ids = [int(machine.machineID) for machine in machinery]
    machinery_name_map = {str(machine.machineID): machine.machineryName for machine in machinery}
    
    
    recipe_code_prefix = packing.product_code.split('.')[0] if '.' in packing.product_code else packing.product_code

    related_packings = Packing.query.filter(
        Packing.week_commencing == packing.week_commencing,
        Packing.product_code.ilike(f"{recipe_code_prefix}%")
    ).all()
    related_fillings = Filling.query.join(Joining, Filling.fill_code == Joining.filling_code).filter(
        Filling.week_commencing == packing.week_commencing,
        Joining.fg_code.ilike(f"{recipe_code_prefix}%")
    ).all()
    total_kilo_per_size = sum(filling.kilo_per_size or 0 for filling in related_fillings)
    related_productions = Production.query.join(Joining, Production.production_code == Joining.production).filter(
        Production.week_commencing == packing.week_commencing,
        Joining.fg_code.ilike(f"{recipe_code_prefix}%")
    ).all()
    total_production_kg = sum(production.total_kg or 0 for production in related_productions)

    return render_template('packing/edit.html',
                         packing=packing,
                         products=products,
                         machinery=machinery,
                         machinery_ids=machinery_ids,
                         machinery_name_map=machinery_name_map,
                         related_packings=related_packings,
                         related_fillings=related_fillings,
                         total_kilo_per_size=total_kilo_per_size,
                         related_productions=related_productions,
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
        logger.error("Error fetching packing autocomplete suggestions:", e)
        return jsonify([])

@packing.route('/packing/search', methods=['GET'])
def get_search_packings():
    # Extract search parameters
    fg_code = request.args.get('fg_code', '').strip()
    description = request.args.get('description', '').strip()
    packing_date = request.args.get('packing_date', '').strip()
    week_commencing = request.args.get('week_commencing', '').strip()

    # Extract sorting parameters as lists
    sort_by = request.args.getlist('sort_by[]') or request.args.getlist('sort_by')
    sort_order = request.args.getlist('sort_order[]') or request.args.getlist('sort_order')

    # Start building the query
    query = Packing.query

    if fg_code:
        query = query.filter(Packing.product_code.ilike(f'%{fg_code}%'))
    if description:
        query = query.filter(Packing.product_description.ilike(f'%{description}%'))
    if packing_date:
        query = query.filter(Packing.packing_date == packing_date)
    if week_commencing:
        query = query.filter(Packing.week_commencing == week_commencing)

    # Apply multi-column sorting
    if sort_by and sort_order and len(sort_by) == len(sort_order):
        for col, order in zip(sort_by, sort_order):
            column_attr = getattr(Packing, col, None)
            if column_attr is not None:
                if order == 'desc':
                    query = query.order_by(desc(column_attr))
                else:
                    query = query.order_by(asc(column_attr))
    else:
        # Default sort if none provided
        query = query.order_by(Packing.week_commencing.desc())

    try:
        packings = query.all()
        # Build response data
        data = []
        for p in packings:
            data.append({
                'id': p.id,
                'week_commencing': str(p.week_commencing) if p.week_commencing else '',
                'packing_date': str(p.packing_date) if p.packing_date else '',
                'product_code': p.product_code,
                'product_description': p.product_description,
                'special_order_kg': p.special_order_kg,
                'special_order_unit': p.special_order_unit,
                'requirement_kg': p.requirement_kg,
                'requirement_unit': p.requirement_unit,
                'avg_weight_per_unit': p.avg_weight_per_unit,
                'soh_requirement_units_week': p.soh_requirement_units_week,
                'soh_kg': p.soh_kg,
                'soh_units': p.soh_units,
                #'avg_weight_per_unit_calc': p.avg_weight_per_unit_calc,
                'machinery': p.machinery,
                'total_stock_kg': p.total_stock_kg,
                'total_stock_units': p.total_stock_units,
                'weekly_average': p.weekly_average,
                'priority': p.priority
            })
        return jsonify({'data': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    

@packing.route('/bulk_edit', methods=['POST'])
def bulk_edit():
    data = request.get_json()
    ids = data.get('ids', [])
    if not ids:
        return jsonify({'success': False, 'message': 'No packing entries selected.'})

    special_order_kg = data.get('special_order_kg')
    weekly_average = data.get('weekly_average')
    machinery = data.get('machinery')
    priority = data.get('priority')

    try:
        for packing_id in ids:
            packing = Packing.query.get(packing_id)
            if not packing:
                continue

            if special_order_kg is not None and special_order_kg != '':
                packing.special_order_kg = float(special_order_kg)
            if weekly_average is not None and weekly_average != '':
                packing.weekly_average = float(weekly_average)
            if machinery is not None and machinery != '':
                packing.machinery = int(machinery)
            else:
                packing.machinery = None
            if priority is not None and priority != '':
                packing.priority = int(priority)

            # Validate machinery
            if packing.machinery is not None:
                machinery_exists = Machinery.query.filter_by(machineID=packing.machinery).first()
                if not machinery_exists:
                    return jsonify({'success': False, 'message': f'Invalid machinery ID {packing.machinery} for packing ID {packing_id}.'})

            # Fetch avg_weight_per_unit from Joining
            joining = Joining.query.filter_by(fg_code=packing.product_code).first()
            if not joining:
                continue
            avg_weight_per_unit = joining.kg_per_unit or 0.0
            packing.avg_weight_per_unit = avg_weight_per_unit

            # Calculate soh_requirement_units_week
            soh = SOH.query.filter_by(fg_code=packing.product_code, week_commencing=packing.week_commencing).first()
            soh_units = soh.soh_total_units if soh else 0
            min_level = joining.min_level or 0.0
            max_level = joining.max_level or 0.0
            packing.soh_requirement_units_week = int(max_level - soh_units) if soh_units < min_level else 0

            # Recalculate fields
            special_order_kg = packing.special_order_kg if packing.special_order_kg is not None else 0
            packing.special_order_unit = int(special_order_kg / avg_weight_per_unit) if avg_weight_per_unit else 0
            packing.soh_kg = round(soh_units * avg_weight_per_unit, 0) if avg_weight_per_unit else 0
            packing.soh_requirement_kg_week = int(packing.soh_requirement_units_week * avg_weight_per_unit) if avg_weight_per_unit else 0
            packing.total_stock_kg = packing.soh_requirement_kg_week * packing.weekly_average if packing.weekly_average is not None else 0
            packing.total_stock_units = round(packing.total_stock_kg / avg_weight_per_unit, 0) if avg_weight_per_unit else 0
            packing.requirement_kg = round(packing.total_stock_kg - packing.soh_kg + special_order_kg, 0) if (packing.total_stock_kg - packing.soh_kg + special_order_kg) > 0 else 0
            packing.requirement_unit = packing.total_stock_units - soh_units + packing.special_order_unit if (packing.total_stock_units - soh_units + packing.special_order_unit) > 0 else 0
            packing.soh_units = soh_units

        db.session.commit()

        # Update related filling and production entries
        for packing_id in ids:
            packing = Packing.query.get(packing_id)
            joining = Joining.query.filter_by(fg_code=packing.product_code).first()
            if joining:
                filling = Filling.query.filter_by(
                    filling_date=packing.packing_date,
                    fill_code=joining.filling_code,
                    week_commencing=packing.week_commencing
                ).first()

                if filling:
                    filling.kilo_per_size = (filling.kilo_per_size or 0.0) + (packing.requirement_kg or 0.0)
                    if filling.kilo_per_size <= 0:
                        db.session.delete(filling)
                else:
                    if (packing.requirement_kg or 0.0) > 0:
                        filling = Filling(
                            filling_date=packing.packing_date,
                            fill_code=joining.filling_code,
                            description=joining.filling_description,
                            kilo_per_size=packing.requirement_kg,
                            week_commencing=packing.week_commencing
                        )
                        db.session.add(filling)
                db.session.commit()

                update_production_entry(packing.packing_date, joining.filling_code, joining, packing.week_commencing)

        return jsonify({'success': True, 'message': 'Packing entries updated successfully!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})



@packing.route('/export', methods=['GET'])
def export_packings():
    try:
        search_fg_code = request.args.get('fg_code', '').strip()
        search_description = request.args.get('description', '').strip()
        search_week_commencing = request.args.get('week_commencing', '').strip()
        search_packing_date = request.args.get('packing_date', '').strip()
        sort_columns = request.args.getlist('sort_by')
        sort_orders = request.args.getlist('sort_order')

        packings_query = Packing.query
        if search_fg_code:
            packings_query = packings_query.filter(Packing.product_code.ilike(f"%{search_fg_code}%"))
        if search_description:
            packings_query = packings_query.filter(Packing.product_description.ilike(f"%{search_description}%"))
        if search_week_commencing:
            try:
                week_commencing_date = datetime.strptime(search_week_commencing, '%Y-%m-%d').date()
                packings_query = packings_query.filter(Packing.week_commencing == week_commencing_date)
            except ValueError:
                flash('Invalid Week Commencing date format. Use YYYY-MM-DD.', 'danger')
                return redirect(url_for('packing.packing_list'))
        if search_packing_date:
            try:
                packing_date = datetime.strptime(search_packing_date, '%Y-%m-%d').date()
                packings_query = packings_query.filter(Packing.packing_date == packing_date)
            except ValueError:
                flash('Invalid Packing Date format. Use YYYY-MM-DD.', 'danger')
                return redirect(url_for('packing.packing_list'))

        if sort_columns and sort_orders:
            order_clauses = []
            for col, order in zip(sort_columns, sort_orders):
                if hasattr(Packing, col):
                    column = getattr(Packing, col)
                    order_clauses.append(column.asc() if order.lower() == 'asc' else column.desc())
            if order_clauses:
                packings_query = packings_query.order_by(*order_clauses)

        packings = packings_query.all()
        packing_data = []

        def get_monday_of_week(dt):
            return dt - timedelta(days=dt.weekday())

        for packing in packings:
            week_commencing = packing.week_commencing or get_monday_of_week(packing.packing_date)
            soh = SOH.query.filter_by(fg_code=packing.product_code, week_commencing=week_commencing).first()
            soh_units = soh.soh_total_units if soh else 0
            joining = Joining.query.filter_by(fg_code=packing.product_code).first()
            avg_weight_per_unit = joining.kg_per_unit if joining else 0.0
            min_level = joining.min_level or 0.0 if joining else 0.0
            max_level = joining.max_level or 0.0 if joining else 0.0
            soh_requirement_units_week = int(max_level - soh_units) if soh_units < min_level else 0

            special_order_kg = packing.special_order_kg if packing.special_order_kg is not None else 0
            special_order_unit = int(special_order_kg / avg_weight_per_unit) if avg_weight_per_unit else 0
            soh_kg = round(soh_units * avg_weight_per_unit, 0) if avg_weight_per_unit else 0
            soh_requirement_kg_week = int(soh_requirement_units_week * avg_weight_per_unit) if avg_weight_per_unit else 0
            total_stock_kg = soh_requirement_kg_week * packing.weekly_average if packing.weekly_average is not None else 0
            total_stock_units = round(total_stock_kg / avg_weight_per_unit, 0) if avg_weight_per_unit else 0
            requirement_kg = round(total_stock_kg - soh_kg + special_order_kg, 0) if (total_stock_kg - soh_kg + special_order_kg) > 0 else 0
            requirement_unit = total_stock_units - soh_units + special_order_unit if (total_stock_units - soh_units + special_order_unit) > 0 else 0

            packing_data.append({
                'Packing Date': packing.packing_date.strftime('%Y-%m-%d') if packing.packing_date else '',
                'Week Commencing': week_commencing.strftime('%Y-%m-%d') if week_commencing else '',
                'Product Code': packing.product_code or '',
                'Product Description': packing.product_description or '',
                'Special Order KG': packing.special_order_kg if packing.special_order_kg is not None else '',
                'Special Order Unit': special_order_unit,
                'Requirement KG': requirement_kg,
                'Requirement Unit': requirement_unit,
                'AVG Weight per Unit': packing.avg_weight_per_unit if packing.avg_weight_per_unit is not None else '',
                'SOH Req KG/Week': soh_requirement_kg_week,
                'SOH Req Units/Week': soh_requirement_units_week,
                'SOH KG': soh_kg,
                'SOH Units': soh_units,
                'Machinery': packing.machinery or '',
                'Total Stock KG': total_stock_kg,
                'Total Stock Units': total_stock_units,
                'Weekly Average': packing.weekly_average if packing.weekly_average is not None else '',
                'Priority': packing.priority or ''
            })

        if not packing_data:
            flash('No data to export after applying filters.', 'warning')
            return redirect(url_for('packing.packing_list'))

        df = pd.DataFrame(packing_data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Packing Data')
        output.seek(0)

        return send_file(
            output,
            download_name=f"packing_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            as_attachment=True,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        logger.error(f"Error exporting to Excel: {str(e)}")
        flash(f"Error exporting to Excel: {str(e)}", 'danger')
        return redirect(url_for('packing.packing_list'))

def update_production_entry(filling_date, fill_code, joining, week_commencing=None):
    """Helper function to create or update a Production entry."""
    try:
        # Get production_code and description from Joining
        production_code = joining.production
        product_description = joining.product_description

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
            production.description = product_description #description 
            production.total_kg = total_kg
            production.batches = batches
            production.week_commencing = week_commencing  # Set week_commencing
        else:
            # Create new Production entry
            production = Production(
                production_date=filling_date,
                production_code=production_code,
                description=product_description,
                batches=batches,
                total_kg=total_kg,
                week_commencing=week_commencing  # Set week_commencing
            )
            db.session.add(production)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating Production entry: {str(e)}", 'error')

@packing.route('/update_cell', methods=['POST'])
def update_cell():
    try:
        data = request.get_json()
        packing_id = data.get('id')
        field = data.get('field')
        value = data.get('value')

        packing = Packing.query.get_or_404(packing_id)

        original_requirement_kg = packing.requirement_kg or 0.0

        if field == 'special_order_kg' or field == 'weekly_average':
            value = float(value) if value else 0.0
        elif field == 'priority':
            value = int(value) if value else 0
        elif field == 'machinery':
            # handle both string and integer inputs for machinery
            if value is not None:
                # Convert to String first to handle both types
                value_str = str(value).strip()
                if value_str:
                    value
                else:
                    value = None
            else:
                value = None

        setattr(packing, field, value)

        # Recalculate dependent fields
        joining = Joining.query.filter_by(fg_code=packing.product_code).first()
        if not joining:
            return jsonify({"success": False, "message": f"No Joining record found for {packing.product_code}."}), 400

        avg_weight_per_unit = joining.kg_per_unit or 0.0
        packing.avg_weight_per_unit = avg_weight_per_unit

        # Fetch SOH data
        soh = SOH.query.filter_by(fg_code=packing.product_code, week_commencing=packing.week_commencing).first()
        soh_units = soh.soh_total_units if soh else 0

        min_level = joining.min_level or 0.0
        max_level = joining.max_level or 0.0
        packing.soh_requirement_units_week = int(max_level - soh_units) if soh_units < min_level else 0

        # Update calculated fields
        special_order_kg = packing.special_order_kg if packing.special_order_kg is not None else 0
        packing.special_order_unit = int(special_order_kg / avg_weight_per_unit) if avg_weight_per_unit else 0
        packing.soh_kg = round(soh_units * avg_weight_per_unit, 0) if avg_weight_per_unit else 0
        packing.soh_requirement_kg_week = int(packing.soh_requirement_units_week * avg_weight_per_unit) if avg_weight_per_unit else 0
        packing.total_stock_kg = packing.soh_requirement_kg_week * packing.weekly_average if packing.weekly_average is not None else 0
        packing.total_stock_units = round(packing.total_stock_kg / avg_weight_per_unit, 0) if avg_weight_per_unit else 0
        packing.requirement_kg = round(packing.total_stock_kg - packing.soh_kg + special_order_kg, 0) if (packing.total_stock_kg - packing.soh_kg + special_order_kg) > 0 else 0
        packing.requirement_unit = packing.total_stock_units - soh_units + packing.special_order_unit if (packing.total_stock_units - soh_units + packing.special_order_unit) > 0 else 0
        packing.soh_units = soh_units

        # Aggregate delta_kg for related packings
        recipe_code_prefix = packing.product_code.split('.')[0]
        related_packings = Packing.query.filter(
            Packing.week_commencing == packing.week_commencing,
            Packing.product_code.ilike(f"{recipe_code_prefix}%")
        ).all()

        total_new_requirement_kg = sum(p.requirement_kg or 0.0 for p in related_packings)
        original_total_requirement_kg = sum(p.requirement_kg or 0.0 for p in related_packings if p.id != packing.id) + original_requirement_kg
        delta_kg = total_new_requirement_kg - original_total_requirement_kg

        db.session.commit()

        # Update Filling and Production
        filling = Filling.query.filter_by(
            filling_date=packing.packing_date,
            fill_code=joining.filling_code,
            week_commencing=packing.week_commencing
        ).first()

        if filling:
            filling.kilo_per_size = (filling.kilo_per_size or 0.0) + delta_kg
            if filling.kilo_per_size <= 0:
                db.session.delete(filling)
        else:
            if delta_kg > 0:
                filling = Filling(
                    filling_date=packing.packing_date,
                    fill_code=joining.filling_code,
                    description=joining.filling_description,
                    kilo_per_size=delta_kg,
                    week_commencing=packing.week_commencing
                )
                db.session.add(filling)

        db.session.commit()

        update_production_entry(packing.packing_date, joining.filling_code, joining, packing.week_commencing)

        return jsonify({"success": True, "message": "Cell updated successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    
@packing.route('/machinery_options', methods=['GET'])
def get_machinery_options():
    try:
        machinery = Machinery.query.all()
        data = [{"id": m.machineID, "name": m.machineryName} for m in machinery]
        return jsonify({"data": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500