from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, session
import pandas as pd
from models.machinery import Machinery
from models.packing import Packing
from models.production import Production
from models.soh import SOH
from models.filling import Filling
from models.item_master import ItemAllergen, ItemMaster
from models.allergen import Allergen
from datetime import date, datetime, timedelta
from database import db
from sqlalchemy import asc, desc
import io
import logging
import math

# Import the update_production_entry function from filling_controller
from controllers.filling_controller import update_production_entry

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

packing_bp = Blueprint('packing', __name__, template_folder='templates')

def re_aggregate_filling_and_production_for_week(week_commencing):
    """
    Re-aggregate all production entries for a specific week based on all packing requirements.
    Uses the BOM service to properly handle recipe explosion.
    """
    try:
        if not week_commencing:
            logger.error("Cannot re-aggregate without a week_commencing date.")
            return False, "Missing week commencing date."

        logger.info(f"Re-aggregating downstream entries for week {week_commencing}")
        
        from controllers.bom_service import BOMService
        success = BOMService.update_downstream_requirements(week_commencing)
        
        if not success:
            error_msg = f"Failed to create downstream entries for week {week_commencing}"
            logger.error(error_msg)
            return False, error_msg
            
        success_msg = f"Successfully re-aggregated downstream entries for week {week_commencing}"
        logger.info(success_msg)
        return True, success_msg
        
    except Exception as e:
        error_msg = f"Failed to re-aggregate production: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg

def create_or_update_soh_entry(product_code, week_commencing, soh_units=0):
    """Create or update SOH entry for a product if it doesn't exist."""
    try:
        # First get the ItemMaster record to get the item_id
        item = ItemMaster.query.filter_by(item_code=product_code).first()
        if not item:
            logger.error(f"No ItemMaster record found for product_code {product_code}")
            return None
            
        soh = SOH.query.filter_by(fg_code=product_code, week_commencing=week_commencing).first()
        if not soh:
            # Create new SOH entry with proper foreign key relationship
            new_soh = SOH(
                item_id=item.id,  # Set the foreign key to ItemMaster
                fg_code=product_code,  # Keep for backward compatibility
                week_commencing=week_commencing,
                soh_total_units=soh_units,
                description=item.description,  # Set description from ItemMaster
                edit_date=datetime.now()
            )
            db.session.add(new_soh)
            db.session.commit()
            logger.info(f"Created new SOH entry for {product_code} (item_id: {item.id}) with {soh_units} units")
            return new_soh
        return soh
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating SOH entry for {product_code}: {str(e)}")
        return None

def update_packing_entry(fg_code, description, packing_date=None, special_order_kg=0.0, avg_weight_per_unit=None, 
                         soh_requirement_units_week=None, calculation_factor=None, week_commencing=None, machinery=None, create_soh=False, current_soh_units=0):
    try:
        # Convert packing_date to date object if it's a string
        if isinstance(packing_date, str):
            try:
                packing_date = datetime.strptime(packing_date, '%d-%m-%Y').date()
            except ValueError:
                return False, "Invalid packing_date format. Please use 'DD-MM-YYYY'."
        packing_date = packing_date or date.today()

        # Get the item master record
        item = ItemMaster.query.filter_by(item_code=fg_code).first()
        if not item:
            return False, f"Item {fg_code} not found"

        # Use provided week_commencing, or calculate it if not provided
        if week_commencing is None:
            def get_monday_of_week(dt):
                return dt - timedelta(days=dt.weekday())
            week_commencing = get_monday_of_week(packing_date)

        # Check for existing packing entry
        packing = Packing.query.filter_by(
            item_id=item.id,
            packing_date=packing_date,
            week_commencing=week_commencing,
            machinery_id=machinery
        ).first()

        if not packing:
            packing = Packing(
                item_id=item.id,
                packing_date=packing_date,
                week_commencing=week_commencing,
                machinery_id=machinery
            )
            db.session.add(packing)

        # Update packing fields
        packing.special_order_kg = special_order_kg
        packing.avg_weight_per_unit = avg_weight_per_unit
        packing.soh_requirement_units_week = soh_requirement_units_week
        packing.calculation_factor = calculation_factor
        
        # Calculate requirement_kg and requirement_unit based on SOH requirements
        if soh_requirement_units_week and avg_weight_per_unit:
            # Calculate what we need to pack in KG
            requirement_kg = soh_requirement_units_week * avg_weight_per_unit
            requirement_unit = soh_requirement_units_week
            
            # Add special order to requirements
            if special_order_kg and special_order_kg > 0:
                requirement_kg += special_order_kg
                special_order_units = special_order_kg / avg_weight_per_unit if avg_weight_per_unit > 0 else 0
                requirement_unit += special_order_units
                
            packing.requirement_kg = round(requirement_kg, 1)
            packing.requirement_unit = int(requirement_unit)
        else:
            # If no requirements, set to 0
            packing.requirement_kg = 0.0
            packing.requirement_unit = 0

        db.session.commit()

        # Create SOH entry if requested
        if create_soh:
            # For new packing entries, create SOH with 0 units (current stock level)
            # The requirement is what we need to pack to reach max_level
            create_or_update_soh_entry(fg_code, week_commencing, current_soh_units)

        return True, "Packing entry updated successfully"

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating packing entry: {str(e)}", exc_info=True)
        return False, str(e)

@packing_bp.route('/packing/')
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
                                        machinery_list=Machinery.query.all(),
                                        current_page="packing")
        except ValueError:
            flash("Invalid Packing Date format.", 'error')
            
    # Always join with ItemMaster to get item details
    packings_query = packings_query.join(ItemMaster, Packing.item_id == ItemMaster.id)
            
    if search_fg_code:
        packings_query = packings_query.filter(ItemMaster.item_code.ilike(f"%{search_fg_code}%"))
    if search_description:
        packings_query = packings_query.filter(ItemMaster.description.ilike(f"%{search_description}%"))

    packings = packings_query.all()
    packing_data = []
    total_requirement_kg = 0
    total_requirement_unit = 0

    for packing in packings:
        # Get SOH data using foreign key relationship
        soh = SOH.query.filter_by(item_id=packing.item_id, week_commencing=packing.week_commencing).first()
        soh_units = soh.soh_total_units if soh else 0

        # Get Item Master data using foreign key relationship
        item = packing.item
        avg_weight_per_unit = item.avg_weight_per_unit if item else 0.0

        # Calculate special order unit
        special_order_unit = round(packing.special_order_kg / avg_weight_per_unit) if packing.special_order_kg and avg_weight_per_unit else 0

        # Calculate SOH kg
        soh_kg = round(soh_units * avg_weight_per_unit, 0) if avg_weight_per_unit else 0

        # Calculate requirement kg and unit
        requirement_kg = packing.requirement_kg if packing.requirement_kg else 0
        requirement_unit = packing.requirement_unit if packing.requirement_unit else 0

        # Calculate SOH requirement kg/week # changed from 4 to avg_weight_per_unit
        soh_requirement_kg_week = requirement_kg * avg_weight_per_unit if requirement_kg else 0

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
            'machinery': {'machine_name': packing.machinery.machineryName} if packing.machinery else None,
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
                         machinery_list=Machinery.query.all(),
                         current_page="packing")

@packing_bp.route('/create', methods=['GET', 'POST'])
def packing_create():
    if request.method == 'POST':
        try:
            # Validate required fields first
            required_fields = ['packing_date', 'product_code']
            for field in required_fields:
                if not request.form.get(field):
                    flash(f'Missing required field: {field}', 'danger')
                    return redirect(url_for('packing.packing_create'))
            
            # Parse form data with error handling
            try:
                packing_date = datetime.strptime(request.form['packing_date'], '%Y-%m-%d').date()
            except ValueError as e:
                flash(f'Invalid packing date format. Please use YYYY-MM-DD format. Error: {str(e)}', 'danger')
                return redirect(url_for('packing.packing_create'))
                
            product_code = request.form['product_code'].strip()
            
            try:
                special_order_kg = float(request.form['special_order_kg']) if request.form.get('special_order_kg') else 0.0
            except ValueError:
                flash('Invalid special order kg value. Please enter a valid number.', 'danger')
                return redirect(url_for('packing.packing_create'))
                
            try:
                calculation_factor = float(request.form['calculation_factor']) if request.form.get('calculation_factor') else 0.0
            except ValueError:
                flash('Invalid calculation factor value. Please enter a valid number.', 'danger')
                return redirect(url_for('packing.packing_create'))
                
            try:
                week_commencing = datetime.strptime(request.form['week_commencing'], '%Y-%m-%d').date() if request.form.get('week_commencing') else None
            except ValueError as e:
                flash(f'Invalid week commencing date format. Please use YYYY-MM-DD format. Error: {str(e)}', 'danger')
                return redirect(url_for('packing.packing_create'))
                
            # Handle machinery (optional)
            machinery = None
            if request.form.get('machinery') and request.form['machinery'].strip():
                try:
                    machinery = int(request.form['machinery'])
                except ValueError:
                    flash('Invalid machinery ID. Please select a valid machinery.', 'danger')
                    return redirect(url_for('packing.packing_create'))
                    
            try:
                priority = int(request.form['priority']) if request.form.get('priority') else 0
            except ValueError:
                flash('Invalid priority value. Please enter a valid number.', 'danger')
                return redirect(url_for('packing.packing_create'))

            # Calculate week_commencing if not provided
            if not week_commencing:
                def get_monday_of_week(dt):
                    return dt - timedelta(days=dt.weekday())
                week_commencing = get_monday_of_week(packing_date)

            # Fetch Item Master data - all required parameters for calculation
            item = ItemMaster.query.filter_by(item_code=product_code).first()
            if not item:
                flash(f"No item record found for product code {product_code}.", 'danger')
                return redirect(url_for('packing.packing_create'))

            # Check for duplicate based on uq_packing_week_product_date_machinery
            existing_packing = Packing.query.filter_by(
                week_commencing=week_commencing,
                item_id=item.id,
                packing_date=packing_date,
                machinery_id=machinery
            ).first()

            if existing_packing:
                machinery_name = existing_packing.machinery.machineryName if existing_packing.machinery else "No Machinery"
                flash(f'🔄 DUPLICATE DETECTED: A packing entry already exists for product {product_code} on {packing_date} with {machinery_name}. You have been redirected to EDIT the existing entry (ID: {existing_packing.id}). Note: You can create another entry with a different machinery.', 'info')
                return redirect(url_for('packing.packing_edit', id=existing_packing.id, from_duplicate='true'))

            # Validate machinery if provided
            if machinery is not None:
                machinery_exists = Machinery.query.filter_by(machineID=machinery).first()
                if not machinery_exists:
                    flash(f'Invalid machinery ID {machinery}. Please select a valid machinery.', 'danger')
                    return redirect(url_for('packing.packing_create'))
            
            # Get all ItemMaster parameters for calculation
            avg_weight_per_unit = item.avg_weight_per_unit or item.kg_per_unit or 0.0  # Try avg_weight_per_unit first, then kg_per_unit as fallback
            min_level = item.min_level or 0.0
            max_level = item.max_level or 0.0
            
            # Use calculation_factor from item_master if not provided by user, otherwise use user input
            if calculation_factor == 0.0:  # If user didn't provide calculation_factor, use from item_master
                calculation_factor = item.calculation_factor or 0.0
            
            logger.info(f"Item Master data for {product_code}: avg_weight_per_unit={avg_weight_per_unit}, min_level={min_level}, max_level={max_level}, calculation_factor={calculation_factor}")

            # Get create_soh parameter from form
            create_soh = bool(request.form.get('create_soh_entry'))

            # Fetch SOH data and calculate soh_requirement_units_week
            soh = SOH.query.filter_by(item_id=item.id, week_commencing=week_commencing).first()
            if soh:
                soh_units = soh.soh_total_units or 0
                logger.info(f"Found SOH data for {product_code}: soh_units={soh_units}")
            else:
                if not create_soh:
                    flash(f"No SOH entry exists for {product_code} (week {week_commencing}). Please check 'Create SOH entry' to proceed.", 'warning')
                    return redirect(url_for('packing.packing_create'))
                soh_units = 0

            # Calculate SOH requirement based on min/max levels from ItemMaster
            # If soh_units < min_level, we need (max_level - soh_units) units
            soh_requirement_units_week = int(max_level - soh_units) if soh_units < min_level else 0

            logger.info(f"SOH calculation for {product_code}: soh_units={soh_units}, soh_requirement_units_week={soh_requirement_units_week}")

            # Create the packing entry
            success, message = update_packing_entry(
                fg_code=product_code,
                description=item.description,
                packing_date=packing_date,
                special_order_kg=special_order_kg,
                avg_weight_per_unit=avg_weight_per_unit,
                soh_requirement_units_week=soh_requirement_units_week,
                calculation_factor=calculation_factor,
                week_commencing=week_commencing,
                machinery=machinery,
                create_soh=create_soh,
                current_soh_units=soh_units  # Pass the actual current SOH units for SOH creation
            )

            if success:
                flash(f'✅ SUCCESS: Packing entry created for {product_code}! {message}', 'success')
                
                # Create downstream Filling and Production entries
                try:
                    from controllers.bom_service import BOMService
                    
                    # Create Filling entry for WIPF
                    filling_entry = BOMService.create_filling_entry(
                        item_id=item.id,
                        week_commencing=week_commencing,
                        requirement_kg=0,  # Will be calculated from all packing entries
                        requirement_unit=0
                    )
                    if filling_entry:
                        db.session.commit()
                        flash(f"✅ Created Filling entry for {product_code}", "success")
                    
                    # Create Production entry for WIP
                    production_entry = BOMService.create_production_entry(
                        item_id=item.id,
                        week_commencing=week_commencing,
                        requirement_kg=0,  # Will be calculated from all packing entries
                        requirement_unit=0
                    )
                    if production_entry:
                        db.session.commit()
                        flash(f"✅ Created Production entry for {product_code}", "success")
                        
                except Exception as e:
                    flash(f"Warning: Could not create downstream entries for {product_code}: {str(e)}", "warning")
                    
            else:
                flash(f'⚠️ ERROR: {message}', 'danger')
                return redirect(url_for('packing.packing_create'))

            return redirect(url_for('packing.packing_list', week_commencing=week_commencing.strftime('%Y-%m-%d')))
        except ValueError as e:
            db.session.rollback()
            flash(f'Invalid data format: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating packing entry: {str(e)}', 'danger')
            logger.error(f"Error creating packing entry: {str(e)}")

    # Use foreign key relationship to filter by item type
    products = ItemMaster.query.join(ItemMaster.item_type).filter(
        ItemMaster.item_type.has(type_name='FG') | ItemMaster.item_type.has(type_name='WIPF')
    ).order_by(ItemMaster.item_code).all()
    machinery = Machinery.query.all()
    allergens = Allergen.query.all()
    return render_template('packing/create.html', products=products, machinery=machinery, allergens=allergens, current_page="packing")


@packing_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def packing_edit(id):
    packing = Packing.query.get_or_404(id)

    if request.method == 'POST':
        try:
            # Parse form data with error handling
            try:
                packing_date = datetime.strptime(request.form['packing_date'], '%Y-%m-%d').date()
            except ValueError as e:
                flash(f'Invalid packing date format. Please use YYYY-MM-DD format. Error: {str(e)}', 'danger')
                return redirect(url_for('packing.packing_edit', id=id))
                
            try:
                special_order_kg = float(request.form['special_order_kg']) if request.form.get('special_order_kg') else 0.0
            except ValueError:
                flash('Invalid special order kg value. Please enter a valid number.', 'danger')
                return redirect(url_for('packing.packing_edit', id=id))
                
            try:
                calculation_factor = float(request.form['calculation_factor']) if request.form.get('calculation_factor') else 0.0
            except ValueError:
                flash('Invalid calculation factor value. Please enter a valid number.', 'danger')
                return redirect(url_for('packing.packing_edit', id=id))
                
            try:
                week_commencing = datetime.strptime(request.form['week_commencing'], '%Y-%m-%d').date() if request.form.get('week_commencing') else None
            except ValueError as e:
                flash(f'Invalid week commencing date format. Please use YYYY-MM-DD format. Error: {str(e)}', 'danger')
                return redirect(url_for('packing.packing_edit', id=id))
                
            # Handle machinery (optional)
            machinery = None
            if request.form.get('machinery') and request.form['machinery'].strip():
                try:
                    machinery = int(request.form['machinery'])
                except ValueError:
                    flash('Invalid machinery ID. Please select a valid machinery.', 'danger')
                    return redirect(url_for('packing.packing_edit', id=id))
                    
            try:
                priority = int(request.form['priority']) if request.form.get('priority') else 0
            except ValueError:
                flash('Invalid priority value. Please enter a valid number.', 'danger')
                return redirect(url_for('packing.packing_edit', id=id))

            # Calculate week_commencing if not provided
            if not week_commencing:
                def get_monday_of_week(dt):
                    return dt - timedelta(days=dt.weekday())
                week_commencing = get_monday_of_week(packing_date)

            # Check for duplicate based on uq_packing_week_product_date_machinery
            existing_packing = Packing.query.filter(
                Packing.week_commencing == week_commencing,
                Packing.item_id == packing.item_id,
                Packing.packing_date == packing_date,
                Packing.machinery_id == machinery,
                Packing.id != id  # Exclude current packing entry
            ).first()

            if existing_packing:
                machinery_name = "No Machinery" if machinery is None else f"Machinery ID {machinery}"
                flash(f'🔄 DUPLICATE DETECTED: A packing entry already exists for this product on {packing_date} with {machinery_name}.', 'danger')
                return redirect(url_for('packing.packing_edit', id=id))

            # Validate machinery if provided
            if machinery is not None:
                machinery_exists = Machinery.query.filter_by(machineID=machinery).first()
                if not machinery_exists:
                    flash(f'Invalid machinery ID {machinery}. Please select a valid machinery.', 'danger')
                    return redirect(url_for('packing.packing_edit', id=id))

            # Get all ItemMaster parameters for calculation
            item = packing.item
            avg_weight_per_unit = item.avg_weight_per_unit or item.kg_per_unit or 0.0  # Try avg_weight_per_unit first, then kg_per_unit as fallback
            min_level = item.min_level or 0.0
            max_level = item.max_level or 0.0
            
            # Use calculation_factor from item_master if not provided by user, otherwise use user input
            if calculation_factor == 0.0:  # If user didn't provide calculation_factor, use from item_master
                calculation_factor = item.calculation_factor or 0.0
            
            logger.info(f"Item Master data for {item.item_code}: avg_weight_per_unit={avg_weight_per_unit}, min_level={min_level}, max_level={max_level}, calculation_factor={calculation_factor}")

            # Fetch SOH data and calculate soh_requirement_units_week
            soh = SOH.query.filter_by(item_id=item.id, week_commencing=week_commencing).first()
            if not soh:
                flash(f"No SOH entry exists for {item.item_code} (week {week_commencing}). Please create one first.", 'danger')
                return redirect(url_for('packing.packing_edit', id=id))
            
            soh_units = soh.soh_total_units or 0
            logger.info(f"Found SOH data for {item.item_code}: soh_units={soh_units}")

            # Calculate SOH requirement based on min/max levels from ItemMaster
            # If soh_units < min_level, we need (max_level - soh_units) units
            soh_requirement_units_week = int(max_level - soh_units) if soh_units < min_level else 0

            logger.info(f"SOH calculation for {item.item_code}: soh_units={soh_units}, soh_requirement_units_week={soh_requirement_units_week}")

            # Update the packing entry
            success, message = update_packing_entry(
                fg_code=item.item_code,
                description=item.description,
                packing_date=packing_date,
                special_order_kg=special_order_kg,
                avg_weight_per_unit=avg_weight_per_unit,
                soh_requirement_units_week=soh_requirement_units_week,
                calculation_factor=calculation_factor,
                week_commencing=week_commencing,
                machinery=machinery,
                create_soh=False  # Don't create SOH in edit mode
            )

            if success:
                flash(f'✅ SUCCESS: Packing entry updated for {item.item_code}! {message}', 'success')
            else:
                flash(f'⚠️ ERROR: {message}', 'danger')
                return redirect(url_for('packing.packing_edit', id=id))

            return redirect(url_for('packing.packing_list'))
        except ValueError as e:
            db.session.rollback()
            flash(f'Invalid data format: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating packing entry: {str(e)}', 'danger')
            logger.error(f"Error updating packing entry: {str(e)}")
    
    # GET request - show comprehensive form with production, packing, and filling data
    week_commencing = packing.week_commencing
    
    # Get all production entries for this week
    production_entries = Production.query.filter_by(week_commencing=week_commencing).order_by(Production.production_date).all()
    total_production_kg = sum([prod.total_kg or 0 for prod in production_entries])
    
    # Get production data (recipe family if available)
    production_data = {}
    if production_entries:
        # Try to get recipe family from the first production entry
        first_prod = production_entries[0]
        if first_prod.item and first_prod.item.item_code:
            # Extract recipe family from item code (e.g., "6002" from "6002.1")
            recipe_family = first_prod.item.item_code.split('.')[0] if '.' in first_prod.item.item_code else first_prod.item.item_code
            production_data['recipe_family'] = recipe_family
    
    # Get all packing entries for this week
    packing_entries = Packing.query.filter_by(week_commencing=week_commencing).order_by(Packing.packing_date).all()
    total_packing_kg = sum([pack.requirement_kg or 0 for pack in packing_entries])
    total_packing_units = sum([pack.requirement_unit or 0 for pack in packing_entries])
    
    # Get all filling entries for this week
    filling_entries = Filling.query.filter_by(week_commencing=week_commencing).order_by(Filling.filling_date).all()
    total_filling_kg = sum([fill.kilo_per_size or 0 for fill in filling_entries])
    
    # Get data for form
    products = ItemMaster.query.join(ItemMaster.item_type).filter(
        ItemMaster.item_type.has(type_name='FG') | ItemMaster.item_type.has(type_name='WIPF')
    ).order_by(ItemMaster.item_code).all()
    machinery = Machinery.query.all()
    allergens = Allergen.query.all()

    # Build a mapping of product family code to WIP description
    family_to_description = {}
    for product in products:
        family_code = product.item_code.split('.')[0] if product.item_code else None
        if family_code and family_code not in family_to_description:
            # Find the WIP item for this family code
            wip_item = ItemMaster.query.join(ItemMaster.item_type).filter(
                ItemMaster.item_code == family_code,
                ItemMaster.item_type.has(type_name='WIP')
            ).first()
            
            if wip_item:
                family_to_description[family_code] = wip_item.description
            else:
                # Fallback to product description if no WIP found
                family_to_description[family_code] = product.description

    return render_template('packing/edit.html', 
                         packing=packing,
                         production_entries=production_entries,
                         production_data=production_data,
                         total_production_kg=total_production_kg,
                         packing_entries=packing_entries,
                         total_packing_kg=total_packing_kg,
                         total_packing_units=total_packing_units,
                         filling_entries=filling_entries,
                         total_filling_kg=total_filling_kg,
                         products=products,
                         machinery=machinery,
                         allergens=allergens,
                         current_page="packing",
                         family_to_description=family_to_description)

@packing_bp.route('/delete/<int:id>', methods=['POST'])
def packing_delete(id):
    packing = Packing.query.get_or_404(id)
    week_to_update = packing.week_commencing  # Capture week before deleting

    try:
        db.session.delete(packing)
        db.session.commit()

        # After successfully deleting, re-aggregate the entire week
        success, message = re_aggregate_filling_and_production_for_week(week_to_update)
        
        if success:
            flash(f'✅ Packing entry deleted successfully! {message}', 'success')
        else:
            flash(f'⚠️ Packing entry deleted, but downstream re-aggregation failed: {message}', 'warning')

    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting packing entry: {str(e)}', 'danger')
        logger.error(f"Error deleting packing entry {id}: {e}", exc_info=True)

    return redirect(url_for('packing.packing_list'))

# Autocomplete for Packing Product Code
@packing_bp.route('/autocomplete_packing', methods=['GET'])
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

@packing_bp.route('/search', methods=['GET'])
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
    query = Packing.query.join(ItemMaster, Packing.item_id == ItemMaster.id)

    # Apply filters
    if fg_code:
        query = query.filter(ItemMaster.item_code.ilike(f"%{fg_code}%"))
    if description:
        query = query.filter(ItemMaster.description.ilike(f"%{description}%"))
    if packing_date_start:
        query = query.filter(Packing.packing_date >= datetime.strptime(packing_date_start, '%Y-%m-%d').date())
    if packing_date_end:
        query = query.filter(Packing.packing_date <= datetime.strptime(packing_date_end, '%Y-%m-%d').date())
    if week_commencing:
        query = query.filter(Packing.week_commencing == datetime.strptime(week_commencing, '%Y-%m-%d').date())
    if machinery:
        query = query.filter(Packing.machinery_id == int(machinery))

    # Apply sorting
    if sort_by and sort_order:
        for i in range(len(sort_by)):
            column = sort_by[i]
            direction = sort_order[i]
            
            if column == 'item_code':
                query = query.order_by(desc(ItemMaster.item_code) if direction == 'desc' else asc(ItemMaster.item_code))
            elif column == 'description':
                query = query.order_by(desc(ItemMaster.description) if direction == 'desc' else asc(ItemMaster.description))
            elif column == 'avg_weight_per_unit':
                query = query.order_by(desc(ItemMaster.avg_weight_per_unit) if direction == 'desc' else asc(ItemMaster.avg_weight_per_unit))
            else:
                # For other columns, use the Packing model attributes
                if hasattr(Packing, column):
                    query = query.order_by(desc(getattr(Packing, column)) if direction == 'desc' else asc(getattr(Packing, column)))

    # Execute query
    packings = query.all()

    # Process results
    result = []
    for p in packings:
        # Calculate SOH data
        soh = SOH.query.filter_by(item_id=p.item_id, week_commencing=p.week_commencing).first()
        soh_units = soh.soh_total_units if soh else 0
        avg_weight_per_unit = p.item.avg_weight_per_unit or p.item.kg_per_unit or 0.0

        # Calculate derived values
        special_order_unit = int(p.special_order_kg / avg_weight_per_unit) if avg_weight_per_unit else 0
        soh_kg = round(soh_units * avg_weight_per_unit, 0) if avg_weight_per_unit else 0
        soh_requirement_kg_week = int(p.soh_requirement_units_week * avg_weight_per_unit) if avg_weight_per_unit else 0
        total_stock_kg = soh_requirement_kg_week * p.calculation_factor if p.calculation_factor is not None else 0
        total_stock_units = math.ceil(total_stock_kg / avg_weight_per_unit) if avg_weight_per_unit else 0
        requirement_kg = round(total_stock_kg - soh_kg + p.special_order_kg, 0) if (total_stock_kg - soh_kg + p.special_order_kg) > 0 else 0
        requirement_unit = total_stock_units - soh_units + special_order_unit if (total_stock_units - soh_units + special_order_unit) > 0 else 0

        result.append({
            'id': p.id,
            'week_commencing': p.week_commencing.strftime('%Y-%m-%d'),
            'packing_date': p.packing_date.strftime('%Y-%m-%d'),
            'special_order_kg': p.special_order_kg,
            'special_order_unit': special_order_unit,
            'requirement_kg': requirement_kg,
            'requirement_unit': requirement_unit,
            'soh_requirement_kg_week': soh_requirement_kg_week,
            'soh_requirement_units_week': p.soh_requirement_units_week,
            'soh_kg': soh_kg,
            'soh_units': soh_units,
            'total_stock_kg': total_stock_kg,
            'total_stock_units': total_stock_units,
            'calculation_factor': p.calculation_factor,
            'priority': p.priority,
            'machinery': {'machine_name': p.machinery.machineryName} if p.machinery else None,
            'item': {
                'item_code': p.item.item_code,
                'description': p.item.description,
                'avg_weight_per_unit': p.item.avg_weight_per_unit
            }
        })

    return jsonify({'packings': result})

@packing_bp.route('/check_duplicate', methods=['GET'])
def check_duplicate():
    # Get parameters
    week_commencing = request.args.get('week_commencing')
    packing_date = request.args.get('packing_date')
    product_code = request.args.get('product_code')
    machinery = request.args.get('machinery')

    # Require at least week_commencing, product_code, and packing_date
    if not all([week_commencing, product_code, packing_date]):
        return jsonify({'error': 'Missing required parameters'}), 400

    try:
        # Convert dates
        week_commencing = datetime.strptime(week_commencing, '%Y-%m-%d').date()
        packing_date = datetime.strptime(packing_date, '%Y-%m-%d').date()
        machinery = int(machinery) if machinery and machinery.strip() else None

        # Find the item
        item = ItemMaster.query.filter_by(item_code=product_code).first()
        if not item:
            return jsonify({'error': f'No item found for product code: {product_code}'}), 404

        # Check for existing packing
        query = Packing.query.filter(
            Packing.week_commencing == week_commencing,
            Packing.packing_date == packing_date,
            Packing.item_id == item.id
        )

        if machinery is not None:
            query = query.filter(Packing.machinery_id == machinery)

        exists = query.first() is not None

        return jsonify({'exists': exists})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error checking for duplicate: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@packing_bp.route('/item_master/<int:item_id>/info')
def get_item_master_info(item_id):
    try:
        item = ItemMaster.query.get(item_id)
        if not item:
            return jsonify({'success': False, 'message': 'Item not found'}), 404

        # Get allergen IDs
        allergen_ids = [allergen.allergens_id for allergen in item.allergens]
        
        return jsonify({
            'success': True,
            'item_code': item.item_code,
            'description': item.description,
            'allergen_ids': allergen_ids,  # Include allergen IDs in response
            'category_id': item.category_id,
            'department_id': item.department_id,
            'machinery_id': item.machinery_id,
            'uom_id': item.uom_id,
            'calculation_factor': float(item.calculation_factor) if item.calculation_factor else None,
            'kg_per_unit': float(item.kg_per_unit) if item.kg_per_unit else None,
            'units_per_bag': float(item.units_per_bag) if item.units_per_bag else None,
            'avg_weight_per_unit': float(item.avg_weight_per_unit) if item.avg_weight_per_unit else None
        })
    except Exception as e:
        print(f"Error getting item info: {str(e)}")
        return jsonify({'success': False, 'message': f'Error getting item info: {str(e)}'}), 500

@packing_bp.route('/machinery_options', methods=['GET'])
def machinery_options():
    """Get all available machinery options for dropdown."""
    try:
        machinery = Machinery.query.all()
        result = []
        for machine in machinery:
            result.append({
                'machineID': machine.machineID,
                'machineryName': machine.machineryName
            })
        logger.info(f"Returning {len(result)} machinery options")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error fetching machinery options: {str(e)}")
        return jsonify([])

@packing_bp.route('/manual_re_aggregate', methods=['POST'])
def manual_re_aggregate():
    """Manual re-aggregation endpoint for fixing totals"""
    try:
        data = request.get_json()
        week_commencing_str = data.get('week_commencing')
        
        if not week_commencing_str:
            return jsonify({'success': False, 'message': 'Missing week_commencing'})
        
        week_commencing = datetime.strptime(week_commencing_str, '%Y-%m-%d').date()
        
        success, message = re_aggregate_filling_and_production_for_week(week_commencing)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message})
            
    except Exception as e:
        logger.error(f"Manual re-aggregation failed: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@packing_bp.route('/bulk_edit', methods=['POST'])
def bulk_edit():
    """Handle bulk editing of packing entries"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        packing_ids = data.get('packing_ids', [])
        updates = data.get('updates', {})

        if not packing_ids or not updates:
            return jsonify({'error': 'Missing packing_ids or updates'}), 400

        # Get all affected packings
        packings = Packing.query.filter(Packing.id.in_(packing_ids)).all()
        if not packings:
            return jsonify({'error': 'No packing entries found'}), 404

        # Track which dates need re-aggregation
        dates_to_reaggregate = set()

        # Apply updates to each packing entry
        for packing in packings:
            modified = False
            
            # Update special_order_kg if provided
            if 'special_order_kg' in updates:
                try:
                    new_value = float(updates['special_order_kg'])
                    if packing.special_order_kg != new_value:
                        packing.special_order_kg = new_value
                        modified = True
                except (ValueError, TypeError):
                    pass

            # Update calculation_factor if provided
            if 'calculation_factor' in updates:
                try:
                    new_value = float(updates['calculation_factor'])
                    if packing.calculation_factor != new_value:
                        packing.calculation_factor = new_value
                        modified = True
                except (ValueError, TypeError):
                    pass

            # Update priority if provided
            if 'priority' in updates:
                try:
                    new_value = int(updates['priority'])
                    if packing.priority != new_value:
                        packing.priority = new_value
                        modified = True
                except (ValueError, TypeError):
                    pass

            # Update machinery if provided
            if 'machinery' in updates:
                try:
                    new_value = int(updates['machinery']) if updates['machinery'] else None
                    if packing.machinery_id != new_value:
                        packing.machinery_id = new_value
                        modified = True
                except (ValueError, TypeError):
                    pass

            if modified:
                # Recalculate values based on the updates
                item = packing.item
                avg_weight_per_unit = item.avg_weight_per_unit or item.kg_per_unit or 0.0
                soh = SOH.query.filter_by(item_id=item.id, week_commencing=packing.week_commencing).first()
                soh_units = soh.soh_total_units if soh else 0

                # Calculate derived values
                special_order_unit = int(packing.special_order_kg / avg_weight_per_unit) if avg_weight_per_unit else 0
                soh_kg = round(soh_units * avg_weight_per_unit, 0) if avg_weight_per_unit else 0
                soh_requirement_kg_week = int(packing.soh_requirement_units_week * avg_weight_per_unit) if avg_weight_per_unit else 0
                total_stock_kg = soh_requirement_kg_week * packing.calculation_factor if packing.calculation_factor is not None else 0
                total_stock_units = math.ceil(total_stock_kg / avg_weight_per_unit) if avg_weight_per_unit else 0
                
                # Update packing values
                packing.special_order_unit = special_order_unit
                packing.soh_kg = soh_kg
                packing.total_stock_kg = total_stock_kg
                packing.total_stock_units = total_stock_units
                packing.requirement_kg = round(total_stock_kg - soh_kg + packing.special_order_kg, 0) if (total_stock_kg - soh_kg + packing.special_order_kg) > 0 else 0
                packing.requirement_unit = total_stock_units - soh_units + special_order_unit if (total_stock_units - soh_units + special_order_unit) > 0 else 0

                # Add this date to re-aggregation set
                dates_to_reaggregate.add((packing.packing_date, packing.week_commencing))

        # Commit all changes
        db.session.commit()

        # Re-aggregate filling and production for affected dates
        weeks_to_reaggregate = set(packing.week_commencing for packing in packings if (packing.week_commencing, packing.id) in dates_to_reaggregate)
        for week_commencing in weeks_to_reaggregate:
            re_aggregate_filling_and_production_for_week(week_commencing)

        return jsonify({'success': True, 'message': f'Successfully updated {len(packings)} packing entries'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error during bulk edit: {str(e)}")
        return jsonify({'error': str(e)}), 500

@packing_bp.route('/update_cell', methods=['POST'])
def update_cell():
    """Handle individual cell updates in the packing table"""
    try:
        data = request.get_json()
        logger.debug(f"Update cell request data: {data}")
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        packing_id = data.get('id')
        field = data.get('field')
        value = data.get('value')
        
        logger.debug(f"Updating packing {packing_id}, field {field}, value {value}")

        if not all([packing_id, field]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400

        # Get the packing entry
        packing = Packing.query.get(packing_id)
        if not packing:
            return jsonify({'success': False, 'error': 'Packing entry not found'}), 404

        try:
            # Handle different field types
            if field == 'special_order_kg':
                packing.special_order_kg = float(value) if value else 0.0
            elif field == 'calculation_factor':
                packing.calculation_factor = float(value) if value else 0.0
            elif field == 'priority':
                packing.priority = int(value) if value else 0
            elif field == 'machinery':
                if value:
                    machinery_id = int(value)
                    # Validate that the machinery exists
                    machinery_exists = Machinery.query.filter_by(machineID=machinery_id).first()
                    if not machinery_exists:
                        return jsonify({'success': False, 'error': f'Invalid machinery ID {machinery_id}. Machinery does not exist.'}), 400
                    packing.machinery_id = machinery_id
                else:
                    packing.machinery_id = None
                
                db.session.commit()
                
                # Return success without re-aggregating since machinery change doesn't affect requirements
                return jsonify({
                    'success': True,
                    'updates': {
                        'machinery_id': packing.machinery_id
                    }
                })

            else:
                return jsonify({'success': False, 'error': f'Invalid field: {field}'}), 400

            # Recalculate values
            item = packing.item
            avg_weight_per_unit = item.avg_weight_per_unit or item.kg_per_unit or 0.0
            soh = SOH.query.filter_by(item_id=item.id, week_commencing=packing.week_commencing).first()
            soh_units = soh.soh_total_units if soh else 0

            # Calculate derived values
            special_order_unit = int(packing.special_order_kg / avg_weight_per_unit) if avg_weight_per_unit else 0
            soh_kg = round(soh_units * avg_weight_per_unit, 0) if avg_weight_per_unit else 0
            soh_requirement_kg_week = int(packing.soh_requirement_units_week * avg_weight_per_unit) if avg_weight_per_unit else 0
            total_stock_kg = soh_requirement_kg_week * packing.calculation_factor if packing.calculation_factor is not None else 0
            total_stock_units = math.ceil(total_stock_kg / avg_weight_per_unit) if avg_weight_per_unit else 0

            # Update packing values
            packing.special_order_unit = special_order_unit
            packing.soh_kg = soh_kg
            packing.total_stock_kg = total_stock_kg
            packing.total_stock_units = total_stock_units
            packing.requirement_kg = round(total_stock_kg - soh_kg + packing.special_order_kg, 0) if (total_stock_kg - soh_kg + packing.special_order_kg) > 0 else 0
            packing.requirement_unit = total_stock_units - soh_units + special_order_unit if (total_stock_units - soh_units + special_order_unit) > 0 else 0

            db.session.commit()
            
            # Re-aggregate filling and production
            re_aggregate_filling_and_production_for_week(packing.week_commencing)

            # Return updated values
            return jsonify({
                'success': True,
                'updates': {
                    'special_order_kg': packing.special_order_kg,
                    'special_order_unit': packing.special_order_unit,
                    'requirement_kg': packing.requirement_kg,
                    'requirement_unit': packing.requirement_unit,
                    'soh_kg': packing.soh_kg,
                    'total_stock_kg': packing.total_stock_kg,
                    'total_stock_units': packing.total_stock_units,
                    'calculation_factor': packing.calculation_factor,
                    'priority': packing.priority,
                    'machinery_id': packing.machinery_id
                }
            })

        except (ValueError, TypeError) as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': f'Invalid value for {field}: {str(e)}'}), 400

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating cell: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@packing_bp.route('/export', methods=['GET'])
def export_packings():
    """Export packing data to Excel with applied filters"""
    try:
        # Extract search parameters
        fg_code = request.args.get('fg_code', '').strip()
        description = request.args.get('description', '').strip()
        packing_date_start = request.args.get('packing_date_start', '').strip()
        packing_date_end = request.args.get('packing_date_end', '').strip()
        week_commencing = request.args.get('week_commencing', '').strip()
        machinery = request.args.get('machinery', '').strip()

        # Start building the query
        query = Packing.query.join(ItemMaster, Packing.item_id == ItemMaster.id)

        # Apply filters
        if fg_code:
            query = query.filter(ItemMaster.item_code.ilike(f"%{fg_code}%"))
        if description:
            query = query.filter(ItemMaster.description.ilike(f"%{description}%"))
        if packing_date_start:
            query = query.filter(Packing.packing_date >= datetime.strptime(packing_date_start, '%Y-%m-%d').date())
        if packing_date_end:
            query = query.filter(Packing.packing_date <= datetime.strptime(packing_date_end, '%Y-%m-%d').date())
        if week_commencing:
            query = query.filter(Packing.week_commencing == datetime.strptime(week_commencing, '%Y-%m-%d').date())
        if machinery:
            query = query.filter(Packing.machinery_id == int(machinery))

        # Execute query
        packings = query.all()

        # Prepare data for Excel
        data = []
        for p in packings:
            # Calculate SOH data
            soh = SOH.query.filter_by(item_id=p.item_id, week_commencing=p.week_commencing).first()
            soh_units = soh.soh_total_units if soh else 0
            avg_weight_per_unit = p.item.avg_weight_per_unit or p.item.kg_per_unit or 0.0

            # Calculate derived values
            special_order_unit = int(p.special_order_kg / avg_weight_per_unit) if avg_weight_per_unit else 0
            soh_kg = round(soh_units * avg_weight_per_unit, 0) if avg_weight_per_unit else 0
            soh_requirement_kg_week = int(p.soh_requirement_units_week * avg_weight_per_unit) if avg_weight_per_unit else 0
            total_stock_kg = soh_requirement_kg_week * p.calculation_factor if p.calculation_factor is not None else 0
            total_stock_units = math.ceil(total_stock_kg / avg_weight_per_unit) if avg_weight_per_unit else 0
            requirement_kg = round(total_stock_kg - soh_kg + p.special_order_kg, 0) if (total_stock_kg - soh_kg + p.special_order_kg) > 0 else 0
            requirement_unit = total_stock_units - soh_units + special_order_unit if (total_stock_units - soh_units + special_order_unit) > 0 else 0

            data.append({
                'Week Commencing': p.week_commencing.strftime('%Y-%m-%d'),
                'Packing Date': p.packing_date.strftime('%Y-%m-%d'),
                'Product Code': p.item.item_code,
                'Product Description': p.item.description,
                'Special Order KG': p.special_order_kg,
                'Special Order Unit': special_order_unit,
                'Requirement KG': requirement_kg,
                'Requirement Unit': requirement_unit,
                'AVG Weight per Unit': p.item.avg_weight_per_unit,
                'SOH Req KG/Week': soh_requirement_kg_week,
                'SOH Req Units/Week': p.soh_requirement_units_week,
                'SOH KG': soh_kg,
                'SOH Units': soh_units,
                'Machinery': p.machinery.machineryName if p.machinery else '',
                'Total Stock KG': total_stock_kg,
                'Total Stock Units': total_stock_units,
                'Calculation Factor': p.calculation_factor,
                'Priority': p.priority
            })

        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Packing List', index=False)
        
        output.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'packing_list_{timestamp}.xlsx'
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error exporting packing data: {str(e)}")
        flash('Error exporting data', 'danger')
        return redirect(url_for('packing.packing_list'))

@packing_bp.route('/search_product_codes', methods=['GET'])
def search_product_codes():
    # Check if user is authenticated
    if 'user_id' not in session:
        return jsonify([]), 401
    
    term = request.args.get('term', '')
    if not term or len(term) < 2:
        return jsonify([])
    
    try:
        # Search for product codes that match the term and are FG (Finished Goods)
        items = ItemMaster.query.join(ItemMaster.item_type).filter(
            ItemMaster.item_code.ilike(f'%{term}%'),
            ItemMaster.item_type.has(type_name='FG')
        ).limit(10).all()
        
        # Return list of matching product codes with descriptions
        results = [{
            'product_code': item.item_code,
            'description': item.description or ''
        } for item in items]
        
        return jsonify(results)
    except Exception as e:
        return jsonify([]), 500

@packing_bp.route('/bulk_edit_comprehensive', methods=['GET', 'POST'])
def bulk_edit_comprehensive():
    """Handle bulk editing of packing entries from the comprehensive edit page"""
    if request.method == 'GET':
        # Handle GET request with IDs parameter
        ids = request.args.get('ids', '')
        if not ids:
            flash('No packing entries selected for bulk edit.', 'error')
            return redirect(url_for('packing.packing_list'))
        
        packing_ids = [int(id.strip()) for id in ids.split(',') if id.strip().isdigit()]
        packings = Packing.query.filter(Packing.id.in_(packing_ids)).all()
        
        if not packings:
            flash('No valid packing entries found for bulk edit.', 'error')
            return redirect(url_for('packing.packing_list'))
        
        machinery_list = Machinery.query.order_by(Machinery.machineryName).all()
        
        return render_template('packing/bulk_edit.html', 
                             packings=packings, 
                             machinery=machinery_list,
                             current_page="packing")
    
    elif request.method == 'POST':
        # Handle form submission from comprehensive edit page
        try:
            updated_count = 0
            week_to_reaggregate = None
            
            # Process machinery updates
            for key, value in request.form.items():
                if key.startswith('machinery_') and value:
                    packing_id = key.replace('machinery_', '')
                    pack = Packing.query.get(packing_id)
                    if pack:
                        old_machinery_id = pack.machinery_id
                        new_machinery_id = int(value)
                        
                        if old_machinery_id != new_machinery_id:
                            pack.machinery_id = new_machinery_id
                            updated_count += 1
                            week_to_reaggregate = pack.week_commencing
            
            if updated_count > 0:
                db.session.commit()
                flash(f'Updated machinery for {updated_count} packing entries!', 'success')
                
                # Re-aggregate downstream after bulk update
                if week_to_reaggregate:
                    try:
                        result, message = re_aggregate_filling_and_production_for_week(week_to_reaggregate)
                        if result:
                            flash('Downstream entries recalculated!', 'success')
                        else:
                            flash(f'Updated but re-aggregation failed: {message}', 'warning')
                    except Exception as e:
                        flash(f'Updated but re-aggregation failed: {str(e)}', 'warning')
            else:
                flash('No changes were made.', 'info')
            
            # Return JSON response for AJAX requests
            if request.is_json or request.headers.get('Content-Type') == 'application/json':
                return jsonify({'success': True, 'message': f'Updated {updated_count} entries'})
            
            # For regular form submissions, redirect back to the edit page
            return redirect(request.referrer or url_for('packing.packing_list'))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'Error during bulk update: {str(e)}'
            flash(error_msg, 'error')
            
            if request.is_json or request.headers.get('Content-Type') == 'application/json':
                return jsonify({'success': False, 'message': error_msg})
            
            return redirect(request.referrer or url_for('packing.packing_list'))

@packing_bp.route('/update_machinery/<int:id>', methods=['POST'])
def update_machinery(id):
    """Update machinery for a packing entry"""
    try:
        data = request.get_json()
        if not data or 'machinery_id' not in data:
            return jsonify({'success': False, 'error': 'Missing machinery_id in request'}), 400

        packing = Packing.query.get(id)
        if not packing:
            return jsonify({'success': False, 'error': 'Packing entry not found'}), 404

        machinery_id = data['machinery_id']
        if machinery_id:
            # Validate machinery exists
            machinery = Machinery.query.get(machinery_id)
            if not machinery:
                return jsonify({'success': False, 'error': f'Invalid machinery ID {machinery_id}'}), 400
            packing.machinery_id = machinery_id
        else:
            packing.machinery_id = None

        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Machinery updated successfully'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating machinery: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@packing_bp.route('/update_field/<int:id>', methods=['POST'])
def update_field(id):
    """Update a specific field for a packing entry"""
    try:
        data = request.get_json()
        if not data or 'field' not in data or 'value' not in data:
            return jsonify({'success': False, 'error': 'Missing field or value in request'}), 400

        packing = Packing.query.get(id)
        if not packing:
            return jsonify({'success': False, 'error': 'Packing entry not found'}), 404

        field = data['field']
        value = data['value']

        if field == 'special_order_kg':
            try:
                value = float(value)
                packing.special_order_kg = value
                
                # Recalculate requirement_kg and requirement_unit
                if packing.avg_weight_per_unit:
                    # Calculate special order units
                    special_order_units = value / packing.avg_weight_per_unit if value > 0 else 0
                    
                    # Base requirements from SOH
                    base_kg = (packing.soh_requirement_units_week or 0) * packing.avg_weight_per_unit
                    base_units = packing.soh_requirement_units_week or 0
                    
                    # Add special order to requirements
                    packing.requirement_kg = round(base_kg + value, 1)
                    packing.requirement_unit = int(base_units + special_order_units)
                else:
                    # If no avg_weight_per_unit, just add special order to requirement_kg
                    packing.requirement_kg = value
                    packing.requirement_unit = 0

                db.session.commit()

                # Update downstream entries (filling and production)
                success, message = re_aggregate_filling_and_production_for_week(packing.week_commencing)
                if not success:
                    logger.warning(f"Warning while updating downstream entries: {message}")

                # Get updated filling and production entries
                filling_entries = Filling.query.filter_by(
                    week_commencing=packing.week_commencing,
                    item_id=packing.item_id
                ).all()
                
                production_entries = Production.query.filter_by(
                    week_commencing=packing.week_commencing,
                    item_id=packing.item_id
                ).all()

                # Format the entries for response
                filling_data = [{
                    'id': fill.id,
                    'kilo_per_size': fill.kilo_per_size
                } for fill in filling_entries]

                production_data = [{
                    'id': prod.id,
                    'total_kg': prod.total_kg,
                    'batches': prod.batches
                } for prod in production_entries]

                return jsonify({
                    'success': True,
                    'message': 'Special order KG updated successfully',
                    'requirement_kg': packing.requirement_kg,
                    'requirement_unit': packing.requirement_unit,
                    'filling_entries': filling_data,
                    'production_entries': production_data
                })
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid numeric value'}), 400
        else:
            return jsonify({'success': False, 'error': f'Field {field} cannot be updated'}), 400

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating field: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

