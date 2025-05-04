from database import db
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy.orm import relationship
from sqlalchemy import String, Integer, DECIMAL, Boolean, Date, ForeignKey, func
import sqlalchemy.exc
from decimal import Decimal
from dotenv import load_dotenv
from sqlalchemy.sql import text
import os


def create_app():
    # Load environment variables from .env file
    load_dotenv()

    # Create and configure the Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret-key')  # Fallback
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Suppress warning

    # Validate SQLALCHEMY_DATABASE_URI
    if not app.config['SQLALCHEMY_DATABASE_URI']:
        raise RuntimeError(
            "SQLALCHEMY_DATABASE_URI is not set. Please define it in the .env file or environment variables."
        )

    # Initialize SQLAlchemy with the app
    db.init_app(app)

    # Register Blueprints
    from controllers.joining_controller import joining_bp
    app.register_blueprint(joining_bp)

    from controllers.soh_controller import soh_bp
    app.register_blueprint(soh_bp)

    from controllers.packing_controller import packing_bp
    app.register_blueprint(packing_bp)

    from controllers.filling_controller import filling_bp
    app.register_blueprint(filling_bp)

    from controllers.production_controller import production_bp
    app.register_blueprint(production_bp)

    from controllers.recipe_controller import recipe_bp
    app.register_blueprint(recipe_bp)

    from controllers.production_plan_controller import production_plan_bp
    app.register_blueprint(production_plan_bp, url_prefix='/production_plan')

    from controllers.inject_products_controller import injected_products_bp
    app.register_blueprint(injected_products_bp)

    # Define routes with deferred model imports
    @app.route('/')
    def index():
        from models import Category  # Defer import
        categories = Category.query.all()
        return render_template('index.html', categories=categories)

    @app.route('/add_department', methods=['POST'])
    def add_department():
        from models import Department
        try:
            department_id = request.form['departmentID']
            department_name = request.form['departmentName']
            new_department = Department(departmentID=department_id, departmentName=department_name)
            db.session.add(new_department)
            db.session.commit()
            flash('Department added successfully!', 'success')
        except sqlalchemy.exc.IntegrityError:
            db.session.rollback()
            flash('Department ID already exists.', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding department: {e}', 'error')
        return redirect(url_for('item_master'))

    @app.route('/add_machine', methods=['POST'])
    def add_machine():
        from models import Machinery
        try:
            machine_id = request.form['machineID']
            machinery_name = request.form['machineryName']
            new_machine = Machinery(machineID=machine_id, machineryName=machinery_name)
            db.session.add(new_machine)
            db.session.commit()
            flash('Machine added successfully!', 'success')
        except sqlalchemy.exc.IntegrityError:
            db.session.rollback()
            flash('Machine ID already exists.', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding machine: {e}', 'error')
        return redirect(url_for('item_master'))

    @app.route('/add_item_type', methods=['POST'])
    def add_item_type():
        from models import ItemType
        try:
            itemTypeID = request.form['itemTypeID']
            itemTypeName = request.form['itemTypeName']
            new_item_type = ItemType(itemTypeID=itemTypeID, itemTypeName=itemTypeName)
            db.session.add(new_item_type)
            db.session.commit()
            flash('Item Type added successfully!', 'success')
        except sqlalchemy.exc.IntegrityError:
            db.session.rollback()
            flash('Item Type ID already exists.', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding item type: {e}', 'error')
        return redirect(url_for('item_master'))

    @app.route('/add_item', methods=['POST'])
    def add_item():
        from models import ItemMaster
        try:
            itemID = request.form['itemID']
            itemName = request.form['itemName']
            itemDescription = request.form['itemDescription']
            itemTypeID = request.form['itemTypeID']
            categoryID = request.form['categoryID']
            departmentID = request.form['departmentID']
            machineID = request.form['machineID']
            kg_per_box = request.form.get('kg_per_box')
            kg_per_each = request.form.get('kg_per_each')
            units_per_box = request.form.get('units_per_box')
            stock_item = 'stock_item' in request.form
            min_stocks_in_boxes = request.form.get('min_stocks_in_boxes')
            max_stocks_in_boxes = request.form.get('max_stocks_in_boxes')
            fill_weight = request.form.get('fill_weight')
            casing = request.form.get('casing')
            ideal_batch_size = request.form.get('ideal_batch_size')

            machineID = None if machineID == '' else machineID

            new_item = ItemMaster(
                itemID=itemID,
                itemName=itemName,
                itemDescription=itemDescription,
                itemTypeID=itemTypeID,
                categoryID=categoryID,
                departmentID=departmentID,
                machineID=machineID,
                kg_per_box=kg_per_box,
                kg_per_each=kg_per_each,
                units_per_box=units_per_box,
                stock_item=stock_item,
                min_stocks_in_boxes=min_stocks_in_boxes,
                max_stocks_in_boxes=max_stocks_in_boxes,
                fill_weight=fill_weight,
                casing=casing,
                ideal_batch_size=ideal_batch_size
            )

            existing_item = ItemMaster.query.filter_by(itemID=itemID).first()
            if existing_item:
                flash(f"Item ID '{itemID}' already exists. Please use a different ID.", 'error')
                return redirect(url_for('item_master'))

            db.session.add(new_item)
            db.session.commit()
            flash('Item added successfully!', 'success')
            return redirect(url_for('item_master'))
        except sqlalchemy.exc.IntegrityError as e:
            db.session.rollback()
            if "Duplicate entry" in str(e) and "PRIMARY" in str(e):
                error_parts = str(e).split("'")
                duplicate_id = error_parts[1] if len(error_parts) > 1 else "unknown"
                flash(f"Item ID '{duplicate_id}' already exists. Please use a different ID.", 'error')
            else:
                flash("Database error occurred. Please try again.", 'error')
            return redirect(url_for('item_master'))
        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred: {str(e)}", 'error')
            return redirect(url_for('item_master'))

    # Create database tables within app context
    with app.app_context():
        # Import models for table creation
        from models import (
            ItemType, Category, Department, Machinery, UOM, ItemMaster, RecipeMaster,
            Joining, SOH, Packing, Filling, Production, InjectedProducts,
            TraceabilityProduction, ProductionPlan, FinishedGoods, Allergen,
            CookingProgram, CookingRecord
        )
        db.create_all()

    return app

# Create the app
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)