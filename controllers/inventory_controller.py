# controllers/inventory_controller.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.inventory import Inventory
from models.raw_materials import RawMaterials
from models.category import Category
from models.production import Production
from database import db
from datetime import datetime

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/inventory')
def list_inventory():
    inventories = Inventory.query.all()
    return render_template('inventory/list.html', inventories=inventories)

@inventory_bp.route('/inventory/create', methods=['GET', 'POST'])
def create_inventory():
    if request.method == 'POST':
        try:
            inventory = Inventory(
                week_commencing=datetime.strptime(request.form['week_commencing'], '%Y-%m-%d'),
                category_id=int(request.form['category_id']),
                raw_material_id=int(request.form['raw_material_id']),
                price_per_kg=float(request.form['price_per_kg']),
                soh=float(request.form['soh']),
                monday=float(request.form['monday']),
                tuesday=float(request.form['tuesday']),
                wednesday=float(request.form['wednesday']),
                thursday=float(request.form['thursday']),
                friday=float(request.form['friday']),
                monday2=float(request.form['monday2']),
                tuesday2=float(request.form['tuesday2']),
                wednesday2=float(request.form['wednesday2']),
                thursday2=float(request.form['thursday2']),
                friday2=float(request.form['friday2'])
            )
            db.session.add(inventory)
            db.session.commit()
            flash('Inventory record created successfully!', 'success')
            return redirect(url_for('inventory.list_inventory'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating inventory record: {str(e)}', 'error')

    categories = Category.query.all()
    raw_materials = RawMaterials.query.all()
    productions = Production.query.all()
    return render_template('inventory/create.html', categories=categories, raw_materials=raw_materials, productions=productions)

@inventory_bp.route('/inventory/edit/<int:id>', methods=['GET', 'POST'])
def edit_inventory(id):
    inventory = Inventory.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            inventory.week_commencing = datetime.strptime(request.form['week_commencing'], '%Y-%m-%d')
            inventory.category_id = int(request.form['category_id'])
            inventory.raw_material_id = int(request.form['raw_material_id'])
            inventory.price_per_kg = float(request.form['price_per_kg'])
            inventory.soh = float(request.form['soh'])
            inventory.monday = float(request.form['monday'])
            inventory.tuesday = float(request.form['tuesday'])
            inventory.wednesday = float(request.form['wednesday'])
            inventory.thursday = float(request.form['thursday'])
            inventory.friday = float(request.form['friday'])
            inventory.monday2 = float(request.form['monday2'])
            inventory.tuesday2 = float(request.form['tuesday2'])
            inventory.wednesday2 = float(request.form['wednesday2'])
            inventory.thursday2 = float(request.form['thursday2'])
            inventory.friday2 = float(request.form['friday2'])
            
            db.session.commit()
            flash('Inventory record updated successfully!', 'success')
            return redirect(url_for('inventory.list_inventory'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating inventory record: {str(e)}', 'error')

    categories = Category.query.all()
    raw_materials = RawMaterials.query.all()
    productions = Production.query.all()
    return render_template('inventory/edit.html', inventory=inventory, categories=categories, raw_materials=raw_materials, productions=productions)

@inventory_bp.route('/inventory/delete/<int:id>', methods=['POST'])
def delete_inventory(id):
    inventory = Inventory.query.get_or_404(id)
    try:
        db.session.delete(inventory)
        db.session.commit()
        flash('Inventory record deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting inventory record: {str(e)}', 'error')
    return redirect(url_for('inventory.list_inventory'))