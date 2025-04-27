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

# Initialize SQLAlchemy without app (will bind to app later)
db = SQLAlchemy()

def create_app():
    # Create and configure the Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Suppress warning

    # Initialize SQLAlchemy with the app
    db.init_app(app)

    # Register the joining Blueprint
    from controllers.joining_controller import joining_bp
    app.register_blueprint(joining_bp)

    # Import models to ensure they are registered with db
    #from models import ItemType, Category, Department, Machinery, UOM, ItemMaster, RecipeMaster, Joining

    # Define routes
    @app.route('/')
    def index():
        with app.app_context():
            categories = Category.query.all()
        return render_template('index.html', categories=categories)

    @app.route('/recipe_search', methods=['GET'])
    def recipe_search():
        search_item_no = request.args.get('item_no', '')
        search_name = request.args.get('name', '')

        with app.app_context():
            query = db.session.query(
                ItemMaster,
                ItemType.itemTypeName,
                Category.categoryName,
                Department.departmentName,
                Machinery.machineryName
            ).outerjoin(ItemType, ItemMaster.itemTypeID == ItemType.itemTypeID)\
             .outerjoin(Category, ItemMaster.categoryID == Category.categoryID)\
             .outerjoin(Department, ItemMaster.departmentID == Department.departmentID)\
             .outerjoin(Machinery, ItemMaster.machineID == Machinery.machineID)

            if search_item_no:
                query = query.filter(ItemMaster.itemID.ilike(f"%{search_item_no}%"))
            if search_name:
                query = query.filter(ItemMaster.itemName.ilike(f"%{search_name}%"))

            items = query.all()

            types = ItemType.query.all()
            categories = Category.query.all()
            departments = Department.query.all()
            machines = Machinery.query.all()

        return render_template('recipe_search.html', 
                             items=items,
                             types=types,
                             categories=categories,
                             departments=departments,
                             machines=machines,
                             search_item_no=search_item_no,
                             search_name=search_name)

    @app.route('/recipe_add', methods=['GET', 'POST'])
    def recipe_add():
        if request.method == 'POST':
            recipeID = request.form.get('recipeID')
            recipeName = request.form.get('recipeName')
            itemID = request.form.get('itemID')
            rawMaterial = request.form.get('rawMaterial')
            usageMaterial = request.form.get('usageMaterial')
            uom = request.form.get('uom')

            try:
                if not all([recipeID, recipeName, itemID, rawMaterial, usageMaterial, uom]):
                    flash("All fields are required.", 'error')
                    return render_template('recipe_add.html')

                usageMaterial = Decimal(usageMaterial)
                with app.app_context():
                    total_usage_for_name = db.session.query(db.func.sum(RecipeMaster.usageMaterial)).filter(RecipeMaster.recipeName == recipeName).scalar()
                    total_usage_for_name = float(total_usage_for_name) if total_usage_for_name else 0.0
                    percentage = (float(usageMaterial) / total_usage_for_name) * 100 if total_usage_for_name else 0

                    new_recipe = RecipeMaster(
                        recipeID=recipeID,
                        recipeName=recipeName,
                        itemID=itemID,
                        rawMaterial=rawMaterial,
                        usageMaterial=usageMaterial,
                        uom=uom,
                        percentage=Decimal(percentage)
                    )

                    db.session.add(new_recipe)
                    db.session.commit()

                flash("Recipe added successfully!", 'success')
                return redirect(url_for('recipe_add'))

            except ValueError:
                flash("Invalid input. Please check your data.", 'error')
                db.session.rollback()
                with app.app_context():
                    recipes = RecipeMaster.query.all()
                return render_template('recipe_add.html', recipes=recipes)

            except sqlalchemy.exc.IntegrityError as e:
                db.session.rollback()
                flash(f"Error: {str(e)}", 'error')
                with app.app_context():
                    recipes = RecipeMaster.query.all()
                return render_template('recipe_add.html', recipes=recipes)

            except Exception as e:
                db.session.rollback()
                flash(f"An unexpected error occurred: {str(e)}", 'error')
                with app.app_context():
                    recipes = RecipeMaster.query.all()
                return render_template('recipe_add.html', recipes=recipes)
        
        with app.app_context():
            recipes = RecipeMaster.query.all()
        return render_template('recipe_add.html', recipes=recipes)

    @app.route('/add_department', methods=['POST'])
    def add_department():
        try:
            department_id = request.form['departmentID']
            department_name = request.form['departmentName']
            new_department = Department(departmentID=department_id, departmentName=department_name)
            with app.app_context():
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
        try:
            machine_id = request.form['machineID']
            machinery_name = request.form['machineryName']
            new_machine = Machinery(machineID=machine_id, machineryName=machinery_name)
            with app.app_context():
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
        try:
            itemTypeID = request.form['itemTypeID']
            itemTypeName = request.form['itemTypeName']
            new_item_type = ItemType(itemTypeID=itemTypeID, itemTypeName=itemTypeName)
            with app.app_context():
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

            with app.app_context():
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

    @app.route('/add_recipe', methods=['POST'])
    def add_recipe():
        recipe_items = []
        current_recipe = {}

        for key, value in request.form.items():
            key_parts = key.split('-')
            if len(key_parts) == 2:
                field_name, item_index = key_parts
                item_index = int(item_index)

                if not current_recipe or current_recipe.get('item_index', None) != item_index:
                    if current_recipe:
                        recipe_items.append(current_recipe)
                    current_recipe = {'item_index': item_index}

                if field_name == 'recipeID':
                    current_recipe['recipeID'] = value
                elif field_name == 'recipeName':
                    current_recipe['recipeName'] = value
                elif field_name == 'itemID':
                    current_recipe['itemID'] = value
                elif field_name == 'rawMaterial':
                    current_recipe['rawMaterial'] = value
                elif field_name == 'usageMaterial':
                    current_recipe['usageMaterial'] = float(value)
                elif field_name == 'uom':
                    current_recipe['uom'] = value

        if current_recipe:
            recipe_items.append(current_recipe)

        percentages = {}
        for item in recipe_items:
            total_usage_for_name = sum(item['usageMaterial'] for item in recipe_items if item['recipeName'] == item['recipeName'])
            percentage = (item['usageMaterial'] / total_usage_for_name) * 100 if total_usage_for_name else 0
            percentages[item['recipeID']] = percentage

        with app.app_context():
            for item in recipe_items:
                new_recipe = RecipeMaster(
                    recipeID=item['recipeID'],
                    recipeName=item['recipeName'],
                    itemID=item['itemID'],
                    rawMaterial=item['rawMaterial'],
                    usageMaterial=item['usageMaterial'],
                    uom=item['uom'],
                    percentage=percentages[item['recipeID']]
                )
                db.session.add(new_recipe)

            db.session.commit()
        return redirect(url_for('recipe_add'))

    @app.route('/autocomplete', methods=['GET'])
    def autocomplete():
        search = request.args.get('query', '').strip()

        if not search:
            return jsonify([])

        try:
            query = text("SELECT itemID, itemName FROM item_master WHERE itemID LIKE :search LIMIT 10")
            with app.app_context():
                results = db.session.execute(query, {"search": search + "%"}).fetchall()
            suggestions = [{"item_no": row[0], "item_name": row[1]} for row in results]
            return jsonify(suggestions)
        except Exception as e:
            print("Error fetching autocomplete suggestions:", e)
            return jsonify([])

    @app.route('/get_search_items', methods=['GET'])
    def get_search_items():
        search_item_no = request.args.get('item_no', '').strip()
        search_name = request.args.get('name', '').strip()

        with app.app_context():
            items_query = ItemMaster.query

            if search_item_no:
                items_query = items_query.filter(ItemMaster.itemID.like(f"{search_item_no}%"))
            if search_name:
                items_query = items_query.filter(ItemMaster.itemName.ilike(f"%{search_name}%"))

            items = items_query.all()

        items_data = [
            {
                "itemID": item.itemID,
                "itemName": item.itemName,
                "itemDescription": item.itemDescription,
                "itemTypeID": item.itemTypeID,
                "categoryID": item.categoryID,
                "departmentID": item.departmentID,
                "machineID": item.machineID,
                "kg_per_box": item.kg_per_box,
                "kg_per_each": item.kg_per_each,
                "units_per_box": item.units_per_box,
                "stock_item": item.stock_item,
                "min_stocks_in_boxes": item.min_stocks_in_boxes,
                "max_stocks_in_boxes": item.max_stocks_in_boxes,
                "fill_weight": item.fill_weight,
                "casing": item.casing,
                "ideal_batch_size": item.ideal_batch_size
            }
            for item in items
        ]

        return jsonify(items_data)

    # Create database tables within app context
    with app.app_context():
        db.create_all()

    return app

# Create the app
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)