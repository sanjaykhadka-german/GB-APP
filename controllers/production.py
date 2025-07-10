from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash
from models.production import Production
from models.item_master import ItemMaster
from database import db
from datetime import datetime

production_bp = Blueprint('production', __name__)

@production_bp.route('/production_list')
def production_list():
    try:
        # Query with relationships
        productions = Production.query.join(
            ItemMaster, Production.item_id == ItemMaster.id
        ).order_by(Production.production_date.desc()).all()
        
        return render_template(
            'production/list.html',
            productions=productions,
            current_page="production"
        )
    except Exception as e:
        # Log the error and return a user-friendly message
        print(f"Error in production_list: {str(e)}")
        return "An error occurred while loading the production list. Please try again.", 500

@production_bp.route('/production/create', methods=['GET', 'POST'])
def production_create():
    if request.method == 'POST':
        try:
            # Handle form submission
            production = Production(
                week_commencing=datetime.strptime(request.form['week_commencing'], '%Y-%m-%d').date(),
                production_date=datetime.strptime(request.form['production_date'], '%Y-%m-%d').date(),
                item_id=request.form['item_id'],
                description=request.form['description'],
                batches=float(request.form['batches']),
                total_kg=float(request.form['total_kg'])
            )
            db.session.add(production)
            db.session.commit()
            flash('Production entry created successfully!', 'success')
            return redirect(url_for('production.production_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating production entry: {str(e)}', 'error')
    
    # GET request - show create form
    items = ItemMaster.query.all()
    return render_template('production/create.html', items=items, current_page="production")

@production_bp.route('/production/edit/<int:id>', methods=['GET', 'POST'])
def production_edit(id):
    production = Production.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            production.week_commencing = datetime.strptime(request.form['week_commencing'], '%Y-%m-%d').date()
            production.production_date = datetime.strptime(request.form['production_date'], '%Y-%m-%d').date()
            production.item_id = request.form['item_id']
            production.description = request.form['description']
            production.batches = float(request.form['batches'])
            production.total_kg = float(request.form['total_kg'])
            
            db.session.commit()
            flash('Production entry updated successfully!', 'success')
            return redirect(url_for('production.production_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating production entry: {str(e)}', 'error')
    
    items = ItemMaster.query.all()
    return render_template('production/edit.html', production=production, items=items, current_page="production")

@production_bp.route('/production/delete/<int:id>')
def production_delete(id):
    try:
        production = Production.query.get_or_404(id)
        db.session.delete(production)
        db.session.commit()
        flash('Production entry deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting production entry: {str(e)}', 'error')
    
    return redirect(url_for('production.production_list'))

@production_bp.route('/production/usage')
def production_usage():
    # Placeholder for usage report
    return render_template('production/usage.html', current_page="production")

@production_bp.route('/production/raw_material_report')
def production_raw_material_report():
    # Placeholder for raw material report
    return render_template('production/raw_material_report.html', current_page="production")

@production_bp.route('/update_daily_plan', methods=['POST'])
def update_daily_plan():
    try:
        data = request.get_json()
        id = data.get('id')
        field = data.get('field')
        value = float(data.get('value', 0))
        
        production = Production.query.get_or_404(id)
        
        if hasattr(production, field) and field in [
            'monday_planned', 'tuesday_planned', 'wednesday_planned',
            'thursday_planned', 'friday_planned', 'saturday_planned', 'sunday_planned'
        ]:
            # Update the specific day's value
            setattr(production, field, value)
            
            # Recalculate total_planned
            production.total_planned = sum([
                production.monday_planned or 0,
                production.tuesday_planned or 0,
                production.wednesday_planned or 0,
                production.thursday_planned or 0,
                production.friday_planned or 0,
                production.saturday_planned or 0,
                production.sunday_planned or 0
            ])
            
            db.session.commit()
            return jsonify({
                'success': True,
                'total_planned': production.total_planned,
                'variance': production.total_kg - production.total_planned
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid field'})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}) 