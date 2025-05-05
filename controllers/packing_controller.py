from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.packing import Packing
from models.soh import SOH
from models.filling import Filling
from models.joining import Joining
from datetime import datetime
from database import db  # Import db from database.py

packing = Blueprint('packing', __name__, url_prefix='/packing')

@packing.route('/')
def packing_list():
    packings = Packing.query.all()
    packing_data = []

    for packing in packings:
        print("its a for loop", packing.product_code)
        
        # Fetch SOH units (J3) from SOH model
        soh = SOH.query.filter_by(fg_code=packing.product_code).first()
        soh_units = soh.soh_total_units if soh else 0  # J3

        # Calculations
        avg_weight_per_unit = packing.avg_weight_per_unit  # F3, K3
        special_order_unit = int(packing.special_order_kg / avg_weight_per_unit) if avg_weight_per_unit else 0  # C3
        soh_kg = round(soh_units * avg_weight_per_unit, 0)  # I3
        soh_requirement_kg_week = int(packing.soh_requirement_units_week * soh_units) if soh_units else 0  # G3
        total_stock_kg = soh_requirement_kg_week * packing.total_stock_multiplier  # L3
        total_stock_unit = round(total_stock_kg / avg_weight_per_unit, 0) if avg_weight_per_unit else 0  # M3
        requirements_kg = (total_stock_kg - soh_kg + packing.special_order_kg) if (total_stock_kg - soh_kg + packing.special_order_kg) > 0 else 0  # D3
        requirements_unit = (total_stock_unit - soh_units + special_order_unit) if (total_stock_unit - soh_units + special_order_unit) > 0 else 0  # E3

        packing_data.append({
            'packing': packing,
            'special_order_unit': special_order_unit,
            'requirements_kg': requirements_kg,
            'requirements_unit': requirements_unit,
            'soh_requirement_kg_week': soh_requirement_kg_week,
            'soh_kg': soh_kg,
            'soh_units': soh_units,
            'total_stock_kg': total_stock_kg,
            'total_stock_unit': total_stock_unit
        })

    return render_template('packing/list.html', packing_data=packing_data)

@packing.route('/create', methods=['GET', 'POST'])
def packing_create():
    if request.method == 'POST':
        try:
            packing_date = datetime.strptime(request.form['packing_date'], '%Y-%m-%d').date()
            product_description = request.form['product_description']
            product_code = request.form['product_code']
            special_order_kg = float(request.form['special_order_kg'])
            avg_weight_per_unit = float(request.form['avg_weight_per_unit'])
            soh_requirement_units_week = int(request.form['soh_requirement_units_week'])
            total_stock_multiplier = float(request.form['total_stock_multiplier'])
            weekly_average = float(request.form['weekly_average']) if request.form['weekly_average'] else None

            # Fetch SOH data for calculations
            soh = SOH.query.filter_by(fg_code=product_code).first()
            soh_units = soh.soh_total_units if soh else 0

            # Calculate requirements_kg
            soh_kg = round(soh_units * avg_weight_per_unit, 0)
            soh_requirement_kg_week = int(soh_requirement_units_week * soh_units) if soh_units else 0
            total_stock_kg = soh_requirement_kg_week * total_stock_multiplier
            requirements_kg = (total_stock_kg - soh_kg + special_order_kg) if (total_stock_kg - soh_kg + special_order_kg) > 0 else 0

            new_packing = Packing(
                packing_date=packing_date,
                product_description=product_description,
                product_code=product_code,
                special_order_kg=special_order_kg,
                avg_weight_per_unit=avg_weight_per_unit,
                soh_requirement_units_week=soh_requirement_units_week,
                total_stock_multiplier=total_stock_multiplier,
                weekly_average=weekly_average,
                requirements_kg=requirements_kg
            )
            db.session.add(new_packing)
            db.session.commit()

            # Create corresponding Filling entry
            joining = Joining.query.filter_by(fg_code=product_code).first()
            if joining:
                new_filling = Filling(
                    filling_date=packing_date,
                    fill_code=joining.filling_code,
                    description=joining.filling_description,
                    kilo_per_size=requirements_kg
                )
                db.session.add(new_filling)
                db.session.commit()
            else:
                flash(f"No Joining record found for fill_code {product_code}. Filling entry not created.", 'warning')

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
    
    return render_template('packing/create.html')

@packing.route('/edit/<int:id>', methods=['GET', 'POST'])
def packing_edit(id):
    packing = Packing.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            packing.packing_date = datetime.strptime(request.form['packing_date'], '%Y-%m-%d').date()
            packing.product_description = request.form['product_description']
            packing.product_code = request.form['product_code']
            packing.special_order_kg = float(request.form['special_order_kg'])
            packing.avg_weight_per_unit = float(request.form['avg_weight_per_unit'])
            packing.soh_requirement_units_week = int(request.form['soh_requirement_units_week'])
            packing.total_stock_multiplier = float(request.form['total_stock_multiplier'])
            packing.weekly_average = float(request.form['weekly_average']) if request.form['weekly_average'] else None

            # Fetch SOH data for calculations
            soh = SOH.query.filter_by(fg_code=packing.product_code).first()
            soh_units = soh.soh_total_units if soh else 0

            # Calculate requirements_kg
            soh_kg = round(soh_units * packing.avg_weight_per_unit, 0)
            soh_requirement_kg_week = int(packing.soh_requirement_units_week * soh_units) if soh_units else 0
            total_stock_kg = soh_requirement_kg_week * packing.total_stock_multiplier
            packing.requirements_kg = (total_stock_kg - soh_kg + packing.special_order_kg) if (total_stock_kg - soh_kg + packing.special_order_kg) > 0 else 0

            db.session.commit()

            # Update or create corresponding Filling entry
            joining = Joining.query.filter_by(fg_code=packing.product_code).first()
            if joining:
                filling = Filling.query.filter_by(fill_code=packing.product_code, filling_date=packing.packing_date).first()
                if filling:
                    # Update existing Filling entry
                    filling.description = joining.filling_description
                    filling.kilo_per_size = packing.requirements_kg
                else:
                    # Create new Filling entry
                    filling = Filling(
                        filling_date=packing.packing_date,
                        fill_code=joining.filling_code,
                        description=joining.filling_description,
                        kilo_per_size=packing.requirements_kg
                    )
                    db.session.add(filling)
                db.session.commit()
            else:
                flash(f"No Joining record found for fill_code {packing.product_code}. Filling entry not updated.", 'warning')

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
    
    return render_template('packing/edit.html', packing=packing)

@packing.route('/delete/<int:id>', methods=['POST'])
def packing_delete(id):
    packing = Packing.query.get_or_404(id)
    try:
        # Optionally delete corresponding Filling entry
        filling = Filling.query.filter_by(fill_code=packing.product_code, filling_date=packing.packing_date).first()
        if filling:
            db.session.delete(filling)
        db.session.delete(packing)
        db.session.commit()
        flash('Packing entry deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting packing entry: {str(e)}', 'danger')
    return redirect(url_for('packing.packing_list'))