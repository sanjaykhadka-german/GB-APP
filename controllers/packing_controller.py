from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from models.machinery import Machinery
from models.packing import Packing
from models.production import Production
from models.soh import SOH
from models.filling import Filling
from models.item_master import ItemMaster
from models.allergen import Allergen
from datetime import date, datetime, timedelta
from database import db
from sqlalchemy.sql import text
from sqlalchemy import asc, desc, func
import pandas as pd
import io
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

packing = Blueprint('packing', __name__, url_prefix='/packing')

def update_packing_entry(fg_code, description, packing_date=None, special_order_kg=0.0, avg_weight_per_unit=None, 
                         soh_requirement_units_week=None, calculation_factor=None, week_commencing=None, machinery=None):
    try:
        # Convert packing_date to date object if it's a string
        if isinstance(packing_date, str):
            try:
                packing_date = datetime.strptime(packing_date, '%d-%m-%Y').date()
            except ValueError:
                return False, "Invalid packing_date format. Please use 'DD-MM-YYYY'."
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

        # Fetch avg_weight_per_unit from Item Master table
        item = ItemMaster.query.filter_by(item_code=fg_code).first()
        if not item:
            return False, f"No item found for fg_code {fg_code}"
        avg_weight_per_unit = avg_weight_per_unit or item.kg_per_unit or item.avg_weight_per_unit or 0.0  # Try kg_per_unit first, then avg_weight_per_unit as fallback

        # Use provided calculation_factor or fetch from existing Packing entry
        packing = Packing.query.filter_by(
            product_code=fg_code, 
            packing_date=packing_date,
            week_commencing=week_commencing,
            machinery=machinery
        ).first()
        
        # If no packing found with the new key structure, try to find by old structure
        if not packing:
            packing = Packing.query.filter_by(
                product_code=fg_code, 
                packing_date=packing_date
            ).first()
            
            # If found with old structure, update it to new structure
            if packing:
                packing.week_commencing = week_commencing
                packing.machinery = machinery

        # Use provided calculation_factor (from item_master) instead of falling back to existing packing
        # This ensures we always use the most up-to-date calculation_factor from item_master
        if calculation_factor is None:
            # Only fall back to existing packing calculation_factor if no calculation_factor was provided
            calculation_factor = packing.calculation_factor if packing else 0.0

        # Calculate soh_requirement_units_week based on SOH and Item Master
        soh_units = soh.soh_total_units if soh else 0
        min_level = item.min_level or 0.0
        max_level = item.max_level or 0.0
        soh_requirement_units_week = soh_requirement_units_week if soh_requirement_units_week is not None else (
            int(max_level - soh_units) if soh_units < min_level else 0
        )

        if not packing:
            packing = Packing(
                product_code=fg_code,
                product_description=description,
                packing_date=packing_date,
                week_commencing=week_commencing,  
                special_order_kg=special_order_kg,
                avg_weight_per_unit=avg_weight_per_unit,
                soh_requirement_units_week=soh_requirement_units_week,
                calculation_factor=calculation_factor,
                machinery=machinery  # Set machinery
            )
            db.session.add(packing)
        else:
            packing.product_description = description
            packing.special_order_kg = special_order_kg
            packing.avg_weight_per_unit = avg_weight_per_unit
            packing.soh_requirement_units_week = soh_requirement_units_week
            packing.calculation_factor = calculation_factor
            packing.week_commencing = week_commencing
            packing.machinery = machinery  # Update machinery

        # Perform calculations
        special_order_kg = packing.special_order_kg if packing.special_order_kg is not None else 0
        packing.special_order_unit = int(special_order_kg / avg_weight_per_unit) if avg_weight_per_unit else 0
        packing.soh_kg = round(soh_units * avg_weight_per_unit, 0) if avg_weight_per_unit else 0
        packing.soh_requirement_kg_week = int(packing.soh_requirement_units_week * avg_weight_per_unit) if avg_weight_per_unit else 0
        packing.total_stock_kg = packing.soh_requirement_kg_week * packing.calculation_factor if packing.calculation_factor is not None else 0
        packing.total_stock_units = round(packing.total_stock_kg / avg_weight_per_unit, 0) if avg_weight_per_unit else 0
        packing.requirement_kg = round(packing.total_stock_kg - packing.soh_kg + special_order_kg, 0) if (packing.total_stock_kg - packing.soh_kg + special_order_kg) > 0 else 0
        packing.requirement_unit = packing.total_stock_units - soh_units + packing.special_order_unit if (packing.total_stock_units - soh_units + packing.special_order_unit) > 0 else 0
        packing.soh_units = soh_units

        db.session.commit()

        # Update Filling and Production entries
        if item and item.filling_code:
            # Find the WIPF item for filling
            wipf_item = ItemMaster.query.filter_by(item_code=item.filling_code, item_type='WIPF').first()
            if wipf_item:
                # Instead of updating just this packing's requirement, we need to aggregate
                # all packing entries that share the same fill_code and date
                
                # Get all packing entries for the same recipe family and date
                recipe_code_prefix = fg_code.split('.')[0]
                related_packings = Packing.query.filter(
                    Packing.week_commencing == week_commencing,
                    Packing.packing_date == packing.packing_date,
                    Packing.product_code.ilike(f"{recipe_code_prefix}%")
                ).all()
                
                # Group by fill_code and calculate total requirement
                fill_code_to_total = {}
                for p in related_packings:
                    p_item = ItemMaster.query.filter_by(item_code=p.product_code).first()
                    if p_item and p_item.filling_code:
                        fill_code = p_item.filling_code
                        if fill_code not in fill_code_to_total:
                            fill_code_to_total[fill_code] = 0
                        fill_code_to_total[fill_code] += (p.requirement_kg or 0.0)
                
                # Update filling entry with aggregated total
                total_requirement_kg = fill_code_to_total.get(item.filling_code, 0.0)
                
                filling = Filling.query.filter_by(
                    filling_date=packing.packing_date,
                    fill_code=item.filling_code,
                    week_commencing=week_commencing
                ).first()

                if filling:
                    filling.kilo_per_size = total_requirement_kg
                    filling.description = wipf_item.description
                    filling.week_commencing = week_commencing
                else:
                    filling = Filling(
                        filling_date=packing.packing_date,
                        fill_code=item.filling_code,
                        description=wipf_item.description,
                        kilo_per_size=total_requirement_kg,
                        week_commencing=week_commencing
                    )
                    db.session.add(filling)
                db.session.commit()

                # For production entry, use the aggregated total from filling
                if item.production_code:
                    wip_item = ItemMaster.query.filter_by(item_code=item.production_code, item_type='WIP').first()
                    if wip_item:
                        update_production_entry(packing.packing_date, item.filling_code, item, week_commencing=week_commencing)
        elif item and item.production_code:
            # Handle items with production_code but no filling_code (direct production)
            logger.info(f"Creating direct production entry for product {fg_code} with production code {item.production_code}")
            
            # Get all packing entries for the same recipe family and date
            recipe_code_prefix = fg_code.split('.')[0]
            related_packings = Packing.query.filter(
                Packing.week_commencing == week_commencing,
                Packing.packing_date == packing.packing_date,
                Packing.product_code.ilike(f"{recipe_code_prefix}%")
            ).all()
            
            # Calculate total requirement for this production code
            total_requirement_kg = sum(p.requirement_kg or 0.0 for p in related_packings 
                                     if ItemMaster.query.filter_by(item_code=p.product_code).first() 
                                     and ItemMaster.query.filter_by(item_code=p.product_code).first().production_code == item.production_code)
            
            # Create or update production entry directly
            create_direct_production_entry(packing.packing_date, item.production_code, total_requirement_kg, week_commencing)
        else:
            logger.warning(f"No item record, filling_code, or production_code found for product code {fg_code}. No entries updated.")

        return True, "Packing entry updated successfully"
    except Exception as e:
        db.session.rollback()
        logger.warning(f"Error updating packing entry for {fg_code}: {str(e)}")
        return False, f"Error updating packing entry: {str(e)}"

@packing.route('/')
def packing_list():
    # Get search parameters from query string
    search_fg_code = request.args.get('fg_code', '').strip()
    search_description = request.args.get('description', '').strip()
    search_week_commencing = request.args.get('week_commencing', '').strip()
    search_packing_date_start = request.args.get('packing_date_start', '').strip()
    search_packing_date_end = request.args.get('packing_date_end', '').strip()

    # Query packings with optional filters
    packings_query = Packing.query
    if search_week_commencing:
        try:
            week_commencing_date = datetime.strptime(search_week_commencing, '%Y-%m-%d').date()
            packings_query = packings_query.filter(Packing.week_commencing == week_commencing_date)
        except ValueError:
            flash("Invalid Week Commencing date format.", 'error')

    # Handle date range filter
    if search_packing_date_start or search_packing_date_end:
        try:
            if search_packing_date_start:
                start_date = datetime.strptime(search_packing_date_start, '%Y-%m-%d').date()
                packings_query = packings_query.filter(Packing.packing_date >= start_date)
            if search_packing_date_end:
                end_date = datetime.strptime(search_packing_date_end, '%Y-%m-%d').date()
                packings_query = packings_query.filter(Packing.packing_date <= end_date)
                
            # Validate date range if both dates are provided
            if search_packing_date_start and search_packing_date_end:
                if start_date > end_date:
                    flash("Start date must be before or equal to end date.", 'error')
                    return render_template('packing/list.html', 
                                        packing_data=[],
                                        search_fg_code=search_fg_code,
                                        search_description=search_description,
                                        search_week_commencing=search_week_commencing,
                                        search_packing_date_start=search_packing_date_start,
                                        search_packing_date_end=search_packing_date_end,
                                        current_page="packing")
        except ValueError:
            flash("Invalid Packing Date format.", 'error')
            
    if search_fg_code:
        packings_query = packings_query.filter(Packing.product_code.ilike(f"%{search_fg_code}%"))
    if search_description:
        packings_query = packings_query.filter(Packing.product_description.ilike(f"%{search_description}%"))

    packings = packings_query.all()
    packing_data = []
    total_requirement_kg = 0
    total_requirement_unit = 0

    for packing in packings:
        # Get SOH data
        soh = SOH.query.filter_by(fg_code=packing.product_code, week_commencing=packing.week_commencing).first()
        soh_units = soh.soh_total_units if soh else 0

        # Get Item Master data for avg_weight_per_unit
        item = ItemMaster.query.filter_by(item_code=packing.product_code).first()
        avg_weight_per_unit = item.kg_per_unit if item else 0.0

        # Calculate special order unit
        special_order_unit = round(packing.special_order_kg / avg_weight_per_unit) if packing.special_order_kg and avg_weight_per_unit else 0

        # Calculate SOH kg
        soh_kg = round(soh_units * avg_weight_per_unit, 0) if avg_weight_per_unit else 0

        # Calculate requirement kg and unit
        requirement_kg = packing.requirement_kg if packing.requirement_kg else 0
        requirement_unit = packing.requirement_unit if packing.requirement_unit else 0

        # Calculate SOH requirement kg/week
        soh_requirement_kg_week = requirement_kg * 4 if requirement_kg else 0

        # Calculate total stock
        total_stock_kg = soh_kg + requirement_kg if soh_kg is not None and requirement_kg is not None else 0
        total_stock_units = soh_units + requirement_unit if soh_units is not None and requirement_unit is not None else 0

        # Get week commencing
        week_commencing = packing.week_commencing

        # Update totals
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
                         search_packing_date_start=search_packing_date_start,
                         search_packing_date_end=search_packing_date_end,
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
            calculation_factor = float(request.form['calculation_factor']) if request.form['calculation_factor'] else 0.0
            week_commencing = datetime.strptime(request.form['week_commencing'], '%Y-%m-%d').date() if request.form['week_commencing'] else None
            machinery = int(request.form['machinery']) if request.form['machinery'] else None
            priority = int(request.form['priority']) if request.form['priority'] else 0

            # Calculate week_commencing if not provided
            if not week_commencing:
                def get_monday_of_week(dt):
                    return dt - timedelta(days=dt.weekday())
                week_commencing = get_monday_of_week(packing_date)

            # Check for duplicate based on uq_packing_week_product_date_machinery
            existing_packing = Packing.query.filter_by(
                week_commencing=week_commencing,
                product_code=product_code,
                packing_date=packing_date,
                machinery=machinery
            ).first()

            if existing_packing:
                flash(f'A packing entry already exists for product {product_code} on {packing_date} (week commencing {week_commencing}) with machinery {machinery}. Please edit the existing entry.', 'warning')
                return redirect(url_for('packing.packing_edit', id=existing_packing.id))

            # Validate machinery if provided
            if machinery is not None:
                machinery_exists = Machinery.query.filter_by(machineID=machinery).first()
                if not machinery_exists:
                    flash(f'Invalid machinery ID {machinery}. Please select a valid machinery.', 'danger')
                    return redirect(url_for('packing.packing_create'))

            # Fetch Item Master data for avg_weight_per_unit
            item = ItemMaster.query.filter_by(item_code=product_code).first()
            if not item:
                flash(f"No item record found for product code {product_code}.", 'danger')
                return redirect(url_for('packing.packing_create'))
            avg_weight_per_unit = item.kg_per_unit or 0.0

            # Fetch SOH data and calculate soh_requirement_units_week
            soh = SOH.query.filter_by(fg_code=product_code, week_commencing=week_commencing).first()
            if not soh:
                flash(f"No SOH entry found for product code {product_code} and week commencing {week_commencing}.", 'danger')
                return redirect(url_for('packing.packing_create'))
            soh_units = soh.soh_total_units if soh else 0
            min_level = item.min_level or 0.0
            max_level = item.max_level or 0.0
            soh_requirement_units_week = int(max_level - soh_units) if soh_units < min_level else 0

            # Perform calculations
            special_order_unit = int(special_order_kg / avg_weight_per_unit) if avg_weight_per_unit else 0
            soh_kg = round(soh_units * avg_weight_per_unit, 0) if avg_weight_per_unit else 0
            soh_requirement_kg_week = int(soh_requirement_units_week * avg_weight_per_unit) if avg_weight_per_unit else 0
            total_stock_kg = soh_requirement_kg_week * calculation_factor if calculation_factor is not None else 0
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
                calculation_factor=calculation_factor,
                week_commencing=week_commencing,
                machinery=machinery,
                priority=priority
            )
            db.session.add(new_packing)
            db.session.commit()

            # Update Filling and Production
            if item and item.filling_code:
                # Find the WIPF item for filling
                wipf_item = ItemMaster.query.filter_by(item_code=item.filling_code, item_type='WIPF').first()
                if wipf_item:
                    existing_filling = Filling.query.filter_by(
                        filling_date=packing_date,
                        fill_code=item.filling_code
                    ).first()

                    if existing_filling:
                        existing_filling.kilo_per_size += requirement_kg
                        existing_filling.description = wipf_item.description
                        existing_filling.week_commencing = week_commencing
                    else:
                        new_filling = Filling(
                            filling_date=packing_date,
                            fill_code=item.filling_code,
                            description=wipf_item.description,
                            kilo_per_size=requirement_kg,
                            week_commencing=week_commencing
                        )
                        db.session.add(new_filling)
                    db.session.commit()

                    # For production entry, find the WIP item
                    if item.production_code:
                        update_production_entry(packing_date, item.filling_code, item, week_commencing)
            elif item and item.production_code:
                # Handle items with production_code but no filling_code (direct production)
                logger.info(f"Creating direct production entry for product {product_code} with production code {item.production_code}")
                create_direct_production_entry(packing_date, item.production_code, requirement_kg, week_commencing)
            else:
                flash(f"No item record, filling_code, or production_code found for product code {product_code}. No entries created.", 'warning')

            flash('Packing entry created successfully!', 'success')
            return redirect(url_for('packing.packing_list'))
        except ValueError as e:
            db.session.rollback()
            flash(f'Invalid data format: {str(e)}', 'danger')
            logger.error(f"Invalid data format: {str(e)}")
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating packing entry: {str(e)}', 'danger')
            logger.error(f"Error creating packing entry: {str(e)}")

    products = ItemMaster.query.filter(ItemMaster.item_type.in_(['FG', 'WIPF'])).order_by(ItemMaster.item_code).all()
    machinery = Machinery.query.all()
    allergens = Allergen.query.all()
    return render_template('packing/create.html', products=products, machinery=machinery, allergens=allergens, current_page="packing")


@packing.route('/edit/<int:id>', methods=['GET', 'POST'])
def packing_edit(id):
    packing = Packing.query.get_or_404(id)

    if request.method == 'POST':
        try:
            original_requirement_kg = packing.requirement_kg or 0.0
            original_packing_date = packing.packing_date  # Store the original packing_date

            # Update packing fields
            packing.packing_date = datetime.strptime(request.form['packing_date'], '%Y-%m-%d').date()
            packing.product_code = request.form['product_code']
            packing.product_description = request.form['product_description']
            packing.special_order_kg = float(request.form['special_order_kg']) if request.form['special_order_kg'] else 0.0
            packing.calculation_factor = float(request.form['calculation_factor']) if request.form['calculation_factor'] else 0.0
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

            # Fetch avg_weight_per_unit from Item Master
            item = ItemMaster.query.filter_by(item_code=packing.product_code).first()
            if not item:
                flash(f"No item record found for {packing.product_code}.", 'danger')
                return redirect(url_for('packing.packing_edit', id=id))
            avg_weight_per_unit = item.kg_per_unit or 0.0
            packing.avg_weight_per_unit = avg_weight_per_unit

            # Calculate soh_requirement_units_week
            soh = SOH.query.filter_by(fg_code=packing.product_code, week_commencing=week_commencing).first()
            soh_units = soh.soh_total_units if soh else 0
            min_level = item.min_level or 0.0
            max_level = item.max_level or 0.0
            packing.soh_requirement_units_week = int(max_level - soh_units) if soh_units < min_level else 0

            # Recalculate fields
            special_order_kg = packing.special_order_kg if packing.special_order_kg is not None else 0
            packing.special_order_unit = int(special_order_kg / avg_weight_per_unit) if avg_weight_per_unit else 0
            packing.soh_kg = round(soh_units * avg_weight_per_unit, 0) if avg_weight_per_unit else 0
            packing.soh_requirement_kg_week = int(packing.soh_requirement_units_week * avg_weight_per_unit) if avg_weight_per_unit else 0
            packing.total_stock_kg = packing.soh_requirement_kg_week * packing.calculation_factor if packing.calculation_factor is not None else 0
            packing.total_stock_units = round(packing.total_stock_kg / avg_weight_per_unit, 0) if avg_weight_per_unit else 0
            packing.requirement_kg = round(packing.total_stock_kg - packing.soh_kg + special_order_kg, 0) if (packing.total_stock_kg - packing.soh_kg + special_order_kg) > 0 else 0
            packing.requirement_unit = packing.total_stock_units - soh_units + packing.special_order_unit if (packing.total_stock_units - soh_units + packing.special_order_unit) > 0 else 0
            packing.soh_units = soh_units
            packing.week_commencing = week_commencing

            db.session.commit()

            # Update Filling and Production entries for all fill_codes in the recipe family
            recipe_code_prefix = packing.product_code.split('.')[0]
            related_packings = Packing.query.filter(
                Packing.week_commencing == packing.week_commencing,
                Packing.product_code.ilike(f"{recipe_code_prefix}%")
            ).all()

            # Group Packing entries by fill_code
            fill_code_to_packing = {}
            for p in related_packings:
                item = ItemMaster.query.filter_by(item_code=p.product_code).first()
                if item and item.filling_code:
                    fill_code = item.filling_code
                    if fill_code not in fill_code_to_packing:
                        fill_code_to_packing[fill_code] = []
                    fill_code_to_packing[fill_code].append(p)

            # Update or consolidate Filling entries
            for fill_code, packings in fill_code_to_packing.items():
                total_requirement_kg = sum(p.requirement_kg or 0.0 for p in packings)
                wipf_item = ItemMaster.query.filter_by(item_code=fill_code, item_type="WIPF").first()
                if not wipf_item:
                    logger.warning(f"No WIPF item found for fill_code {fill_code}. Skipping Filling update.")
                    continue

                # Find existing Filling entry using the *original* packing_date
                existing_filling = Filling.query.filter_by(
                    week_commencing=packing.week_commencing,
                    fill_code=fill_code,
                    filling_date=original_packing_date
                ).first()

                if existing_filling:
                    # Update the existing filling entry with the new packing_date
                    existing_filling.filling_date = packing.packing_date
                    existing_filling.description = wipf_item.description
                    existing_filling.kilo_per_size = total_requirement_kg
                    existing_filling.week_commencing = packing.week_commencing
                    db.session.add(existing_filling)
                else:
                    # Create a new filling entry if none exists
                    if total_requirement_kg > 0:
                        filling = Filling(
                            filling_date=packing.packing_date,
                            fill_code=fill_code,
                            description=wipf_item.description,
                            kilo_per_size=total_requirement_kg,
                            week_commencing=packing.week_commencing
                        )
                        db.session.add(filling)

            # Update or consolidate Production entry  
            production_code = item.production_code if item else None
            if production_code:
                # For items with production code but no filling code, calculate total directly from packings
                if not item.filling_code:
                    # Direct production - sum requirements from all packings with same production code
                    total_production_requirement = sum(p.requirement_kg or 0.0 for p in related_packings 
                                                     if ItemMaster.query.filter_by(item_code=p.product_code).first() 
                                                     and ItemMaster.query.filter_by(item_code=p.product_code).first().production_code == production_code)
                else:
                    # Production via filling - use total from filling entries
                    total_production_requirement = sum(filling.kilo_per_size or 0 for filling in related_fillings)
                
                # Calculate batches
                batch_size = 100.0  # Default batch size
                batches = total_production_requirement / batch_size if total_production_requirement > 0 else 0

                # Find existing Production entry using the *original* packing_date
                existing_production = Production.query.filter_by(
                    week_commencing=packing.week_commencing,
                    production_code=production_code,
                    production_date=original_packing_date
                ).first()

                if existing_production:
                    # Update the existing production entry with the new packing_date
                    existing_production.production_date = packing.packing_date
                    wip_item = ItemMaster.query.filter_by(item_code=production_code, item_type="WIP").first()
                    existing_production.description = wip_item.description if wip_item else f"{production_code} - WIP"
                    existing_production.batches = batches
                    existing_production.total_kg = total_production_requirement
                    existing_production.week_commencing = packing.week_commencing
                    db.session.add(existing_production)
                else:
                    # Create a new production entry if none exists
                    if total_production_requirement > 0:
                        wip_item = ItemMaster.query.filter_by(item_code=production_code, item_type="WIP").first()
                        production = Production(
                            production_date=packing.packing_date,
                            production_code=production_code,
                            description=wip_item.description if wip_item else f"{production_code} - WIP",
                            batches=batches,
                            total_kg=total_production_requirement,
                            week_commencing=packing.week_commencing
                        )
                        db.session.add(production)

            db.session.commit()

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
    products = ItemMaster.query.filter(ItemMaster.item_type.in_(["FG", "WIPF"])).order_by(ItemMaster.item_code).all()
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
    # Get related fillings by finding items with matching filling codes
    related_items_with_filling = ItemMaster.query.filter(
        ItemMaster.item_code.ilike(f"{recipe_code_prefix}%"),
        ItemMaster.filling_code.isnot(None)
    ).all()
    filling_codes = [item.filling_code for item in related_items_with_filling if item.filling_code]
    related_fillings = Filling.query.filter(
        Filling.week_commencing == packing.week_commencing,
        Filling.fill_code.in_(filling_codes)
    ).all() if filling_codes else []
    total_kilo_per_size = sum(filling.kilo_per_size or 0 for filling in related_fillings)
    
    # Get related productions by finding items with matching production codes (regardless of filling code)
    related_items_with_production = ItemMaster.query.filter(
        ItemMaster.item_code.ilike(f"{recipe_code_prefix}%"),
        ItemMaster.production_code.isnot(None)
    ).all()
    production_codes = [item.production_code for item in related_items_with_production if item.production_code]
    related_productions = Production.query.filter(
        Production.week_commencing == packing.week_commencing,
        Production.production_code.in_(production_codes)
    ).all() if production_codes else []
    total_production_kg = sum(production.total_kg or 0 for production in related_productions) if related_productions else 0

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
        item = ItemMaster.query.filter_by(item_code=packing.product_code).first()
        if item and item.filling_code:
            filling = Filling.query.filter_by(
                filling_date=packing.packing_date,
                fill_code=item.filling_code
            ).first()
            if filling:
                filling.kilo_per_size -= packing.requirement_kg
                if filling.kilo_per_size <= 0:
                    db.session.delete(filling)
                else:
                    db.session.commit()
                # Update corresponding Production entry
                update_production_entry(packing.packing_date, item.filling_code, item, packing.week_commencing)

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
        results = ItemMaster.query.filter(
            ItemMaster.item_code.ilike(f"{search}%"),
            ItemMaster.item_type.in_(['FG', 'WIPF'])
        ).limit(10).all()
        suggestions = [{"fg_code": item.item_code, "description": item.description} for item in results]
        return jsonify(suggestions)
    except Exception as e:
        logger.error("Error fetching packing autocomplete suggestions:", e)
        return jsonify([])

@packing.route('/packing/search', methods=['GET'])
def get_search_packings():
    # Extract search parameters
    fg_code = request.args.get('fg_code', '').strip()
    description = request.args.get('description', '').strip()
    packing_date_start = request.args.get('packing_date_start', '').strip()
    packing_date_end = request.args.get('packing_date_end', '').strip()
    week_commencing = request.args.get('week_commencing', '').strip()
    machinery = request.args.get('machinery', '').strip()

    # Extract sorting parameters as lists
    sort_by = request.args.getlist('sort_by[]') or request.args.getlist('sort_by')
    sort_order = request.args.getlist('sort_order[]') or request.args.getlist('sort_order')

    # Start building the query
    query = Packing.query

    if fg_code:
        query = query.filter(Packing.product_code.ilike(f'%{fg_code}%'))
    if description:
        query = query.filter(Packing.product_description.ilike(f'%{description}%'))

    # Handle date range filter
    if packing_date_start or packing_date_end:
        try:
            if packing_date_start:
                start_date = datetime.strptime(packing_date_start, '%Y-%m-%d').date()
                query = query.filter(Packing.packing_date >= start_date)
            if packing_date_end:
                end_date = datetime.strptime(packing_date_end, '%Y-%m-%d').date()
                query = query.filter(Packing.packing_date <= end_date)
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400

    if week_commencing:
        try:
            week_commencing_date = datetime.strptime(week_commencing, '%Y-%m-%d').date()
            query = query.filter(Packing.week_commencing == week_commencing_date)
        except ValueError:
            return jsonify({'error': 'Invalid week commencing date format'}), 400
    
    # Handle machinery filter
    if machinery:
        try:
            machinery_id = int(machinery)
            query = query.filter(Packing.machinery == machinery_id)
        except ValueError:
            return jsonify({'error': 'Invalid machinery ID'}), 400

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
                'machinery': p.machinery,
                'total_stock_kg': p.total_stock_kg,
                'total_stock_units': p.total_stock_units,
                'calculation_factor': p.calculation_factor,
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
    calculation_factor = data.get('calculation_factor')
    machinery = data.get('machinery')
    priority = data.get('priority')

    try:
        for packing_id in ids:
            packing = Packing.query.get(packing_id)
            if not packing:
                continue

            if special_order_kg is not None and special_order_kg != '':
                packing.special_order_kg = float(special_order_kg)
            if calculation_factor is not None and calculation_factor != '':
                packing.calculation_factor = float(calculation_factor)
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

            # Fetch avg_weight_per_unit from ItemMaster
            item = ItemMaster.query.filter_by(item_code=packing.product_code).first()
            if not item:
                continue
            avg_weight_per_unit = item.kg_per_unit or 0.0
            packing.avg_weight_per_unit = avg_weight_per_unit

            # Calculate soh_requirement_units_week
            soh = SOH.query.filter_by(fg_code=packing.product_code, week_commencing=packing.week_commencing).first()
            soh_units = soh.soh_total_units if soh else 0
            min_level = item.min_level or 0.0
            max_level = item.max_level or 0.0
            packing.soh_requirement_units_week = int(max_level - soh_units) if soh_units < min_level else 0

            # Recalculate fields
            special_order_kg = packing.special_order_kg if packing.special_order_kg is not None else 0
            packing.special_order_unit = int(special_order_kg / avg_weight_per_unit) if avg_weight_per_unit else 0
            packing.soh_kg = round(soh_units * avg_weight_per_unit, 0) if avg_weight_per_unit else 0
            packing.soh_requirement_kg_week = int(packing.soh_requirement_units_week * avg_weight_per_unit) if avg_weight_per_unit else 0
            packing.total_stock_kg = packing.soh_requirement_kg_week * packing.calculation_factor if packing.calculation_factor is not None else 0
            packing.total_stock_units = round(packing.total_stock_kg / avg_weight_per_unit, 0) if avg_weight_per_unit else 0
            packing.requirement_kg = round(packing.total_stock_kg - packing.soh_kg + special_order_kg, 0) if (packing.total_stock_kg - packing.soh_kg + special_order_kg) > 0 else 0
            packing.requirement_unit = packing.total_stock_units - soh_units + packing.special_order_unit if (packing.total_stock_units - soh_units + packing.special_order_unit) > 0 else 0
            packing.soh_units = soh_units

        db.session.commit()

        # Update Filling entries for all fill_codes in the recipe family
        recipe_code_prefixes = {Packing.query.get(packing_id).product_code.split('.')[0] for packing_id in ids}
        for prefix in recipe_code_prefixes:
            related_packings = Packing.query.filter(
                Packing.week_commencing == Packing.query.get(packing_id).week_commencing,
                Packing.product_code.ilike(f"{prefix}%")
            ).all()

            # Group Packing entries by fill_code
            fill_code_to_packing = {}
            for p in related_packings:
                item = ItemMaster.query.filter_by(item_code=p.product_code).first()
                if item and item.filling_code:
                    fill_code = item.filling_code
                    if fill_code not in fill_code_to_packing:
                        fill_code_to_packing[fill_code] = []
                    fill_code_to_packing[fill_code].append(p)

            # Update or create Filling entries
            for fill_code, packings in fill_code_to_packing.items():
                total_requirement_kg = sum(p.requirement_kg or 0.0 for p in packings)
                filling = Filling.query.filter_by(
                    filling_date=packings[0].packing_date,
                    fill_code=fill_code,
                    week_commencing=packings[0].week_commencing
                ).first()

                wipf_item = ItemMaster.query.filter_by(item_code=fill_code, item_type="WIPF").first()
                if not wipf_item:
                    logger.warning(f"No WIPF item found for fill_code {fill_code}. Skipping Filling update.")
                    continue

                if filling:
                    filling.kilo_per_size = total_requirement_kg
                    if filling.kilo_per_size <= 0:
                        db.session.delete(filling)
                else:
                    if total_requirement_kg > 0:
                        filling = Filling(
                            filling_date=packings[0].packing_date,
                            fill_code=fill_code,
                            description=wipf_item.description,
                            kilo_per_size=total_requirement_kg,
                            week_commencing=packings[0].week_commencing
                        )
                        db.session.add(filling)
                db.session.commit()

                # Update Production entry
                # Find the original finished good item to get its production code
                original_fg_item = ItemMaster.query.filter_by(item_code=packings[0].product_code).first()
                if original_fg_item:
                    update_production_entry(packings[0].packing_date, fill_code, original_fg_item, packings[0].week_commencing)

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
        machinery = request.args.get('machinery', '').strip()
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
        if machinery:
            try:
                machinery_id = int(machinery)
                packings_query = packings_query.filter(Packing.machinery == machinery_id)
            except ValueError:
                flash('Invalid Machinery ID.', 'danger')
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
            item = ItemMaster.query.filter_by(item_code=packing.product_code).first()
            avg_weight_per_unit = item.kg_per_unit if item else 0.0
            min_level = item.min_level or 0.0 if item else 0.0
            max_level = item.max_level or 0.0 if item else 0.0
            soh_requirement_units_week = int(max_level - soh_units) if soh_units < min_level else 0

            special_order_kg = packing.special_order_kg if packing.special_order_kg is not None else 0
            special_order_unit = int(special_order_kg / avg_weight_per_unit) if avg_weight_per_unit else 0
            soh_kg = round(soh_units * avg_weight_per_unit, 0) if avg_weight_per_unit else 0
            soh_requirement_kg_week = int(soh_requirement_units_week * avg_weight_per_unit) if avg_weight_per_unit else 0
            total_stock_kg = soh_requirement_kg_week * packing.calculation_factor if packing.calculation_factor is not None else 0
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
                'Calculation Factor': packing.calculation_factor if packing.calculation_factor is not None else '',
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

def create_direct_production_entry(production_date, production_code, total_kg, week_commencing=None):
    """Helper function to create or update a Production entry directly (without filling step)."""
    try:
        # Get WIP item for production description
        wip_item = ItemMaster.query.filter_by(item_code=production_code, item_type="WIP").first()
        product_description = wip_item.description if wip_item else f"{production_code} - WIP"

        # If total_kg is 0, delete the Production entry if it exists
        if total_kg == 0.0:
            production = Production.query.filter_by(
                production_date=production_date,
                production_code=production_code,
                week_commencing=week_commencing
            ).first()
            if production:
                db.session.delete(production)
                db.session.commit()
            return

        # Calculate batches (using default batch size of 100kg)
        batch_size = 100.0
        batches = total_kg / batch_size if total_kg > 0 else 0.0

        # Check for existing Production entry
        production = Production.query.filter_by(
            production_date=production_date,
            production_code=production_code,
            week_commencing=week_commencing
        ).first()

        if production:
            # Update existing Production entry
            production.description = product_description
            production.total_kg = total_kg
            production.batches = batches
        else:
            # Create new Production entry
            production = Production(
                production_date=production_date,
                production_code=production_code,
                description=product_description,
                batches=batches,
                total_kg=total_kg,
                week_commencing=week_commencing
            )
            db.session.add(production)

        db.session.commit()
        logger.info(f"Created/updated direct production entry: {production_code}, {total_kg}kg, {batches} batches")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating direct production entry: {str(e)}")

def update_production_entry(filling_date, fill_code, item, week_commencing=None):
    """Helper function to create or update a Production entry."""
    try:
        # Get production_code and description from Item Master
        production_code = item.production_code
        if not production_code:
            return  # No production code, nothing to update
            
        # Get WIP item for production description
        wip_item = ItemMaster.query.filter_by(item_code=production_code, item_type="WIP").first()
        product_description = wip_item.description if wip_item else f"{production_code} - WIP"

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
            production.description = product_description
            production.total_kg = total_kg
            production.batches = batches
            production.week_commencing = week_commencing
        else:
            # Create new Production entry
            production = Production(
                production_date=filling_date,
                production_code=production_code,
                description=product_description,
                batches=batches,
                total_kg=total_kg,
                week_commencing=week_commencing
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

        if field == 'special_order_kg' or field == 'calculation_factor':
            value = float(value) if value else 0.0
        elif field == 'priority':
            value = int(value) if value else 0
        elif field == 'machinery':
            if value is not None:
                value_str = str(value).strip()
                if value_str:
                    value = int(value_str)
                else:
                    value = None
            else:
                value = None

        setattr(packing, field, value)

        # Recalculate dependent fields
        item = ItemMaster.query.filter_by(item_code=packing.product_code).first()
        if not item:
            return jsonify({"success": False, "message": f"No item record found for {packing.product_code}."}), 400

        avg_weight_per_unit = item.kg_per_unit or 0.0
        packing.avg_weight_per_unit = avg_weight_per_unit

        # Fetch SOH data
        soh = SOH.query.filter_by(fg_code=packing.product_code, week_commencing=packing.week_commencing).first()
        soh_units = soh.soh_total_units if soh else 0

        min_level = item.min_level or 0.0
        max_level = item.max_level or 0.0
        packing.soh_requirement_units_week = int(max_level - soh_units) if soh_units < min_level else 0

        # Update calculated fields
        special_order_kg = packing.special_order_kg if packing.special_order_kg is not None else 0
        packing.special_order_unit = int(special_order_kg / avg_weight_per_unit) if avg_weight_per_unit else 0
        packing.soh_kg = round(soh_units * avg_weight_per_unit, 0) if avg_weight_per_unit else 0
        packing.soh_requirement_kg_week = int(packing.soh_requirement_units_week * avg_weight_per_unit) if avg_weight_per_unit else 0
        packing.total_stock_kg = packing.soh_requirement_kg_week * packing.calculation_factor if packing.calculation_factor is not None else 0
        packing.total_stock_units = round(packing.total_stock_kg / avg_weight_per_unit, 0) if avg_weight_per_unit else 0
        packing.requirement_kg = round(packing.total_stock_kg - packing.soh_kg + special_order_kg, 0) if (packing.total_stock_kg - packing.soh_kg + special_order_kg) > 0 else 0
        packing.requirement_unit = packing.total_stock_units - soh_units + packing.special_order_unit if (packing.total_stock_units - soh_units + packing.special_order_unit) > 0 else 0
        packing.soh_units = soh_units

        db.session.commit()

        # Update Filling entries for all fill_codes in the recipe family
        recipe_code_prefix = packing.product_code.split('.')[0]
        related_packings = Packing.query.filter(
            Packing.week_commencing == packing.week_commencing,
            Packing.product_code.ilike(f"{recipe_code_prefix}%")
        ).all()

        # Group Packing entries by fill_code
        fill_code_to_packing = {}
        for p in related_packings:
            item = ItemMaster.query.filter_by(item_code=p.product_code).first()
            if item and item.filling_code:
                fill_code = item.filling_code
                if fill_code not in fill_code_to_packing:
                    fill_code_to_packing[fill_code] = []
                fill_code_to_packing[fill_code].append(p)

        # Update or create Filling entries
        for fill_code, packings in fill_code_to_packing.items():
            total_requirement_kg = sum(p.requirement_kg or 0.0 for p in packings)
            filling = Filling.query.filter_by(
                filling_date=packing.packing_date,
                fill_code=fill_code,
                week_commencing=packing.week_commencing
            ).first()

            wipf_item = ItemMaster.query.filter_by(item_code=fill_code, item_type="WIPF").first()
            if not wipf_item:
                logger.warning(f"No WIPF item found for fill_code {fill_code}. Skipping Filling update.")
                continue

            if filling:
                filling.kilo_per_size = total_requirement_kg
                if filling.kilo_per_size <= 0:
                    db.session.delete(filling)
            else:
                if total_requirement_kg > 0:
                    filling = Filling(
                        filling_date=packing.packing_date,
                        fill_code=fill_code,
                        description=wipf_item.description,
                        kilo_per_size=total_requirement_kg,
                        week_commencing=packing.week_commencing
                    )
                    db.session.add(filling)
            db.session.commit()

            # Update Production entry
            # Find the original finished good item to get its production code
            original_fg_item = ItemMaster.query.filter_by(item_code=packing.product_code).first()
            if original_fg_item:
                update_production_entry(packing.packing_date, fill_code, original_fg_item, packing.week_commencing)

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