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

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
db = SQLAlchemy(app)

# models here (ItemType, Category, Department, RawMaterialMaster, RecipeMaster, ItemMaster, SOH_Master, ProductionPlanMaster)

class ItemType(db.Model):
    __tablename__ = 'item_type'
    itemTypeID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    itemTypeName = db.Column(db.String(50), nullable=False)

class Category(db.Model):
    __tablename__ = 'category'
    categoryID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    categoryName = db.Column(db.String(50), nullable=False, unique=True)

class Department(db.Model):
    __tablename__ = 'department'
    departmentID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    departmentName = db.Column(db.String(50), nullable=False, unique=True)


class Machinery(db.Model):
    __tablename__ = 'machinery'
    machineID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    machineryName = db.Column(db.String(50), nullable=False, unique=True)

class UOM(db.Model):
    __tablename__ = 'uom_type'
    UOMID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UOMName = db.Column(db.String(50), nullable=False)


class ItemMaster(db.Model):
    __tablename__ = 'item_master'
    itemID = db.Column(db.String(255), primary_key=True)
    itemName = db.Column(db.String(255), nullable=False)
    itemDescription = db.Column(db.String(255))
    itemTypeID = db.Column(db.String(255), db.ForeignKey('item_type.itemTypeID'))
    categoryID = db.Column(db.String(255), db.ForeignKey('category.categoryID'))
    departmentID = db.Column(db.String(255), db.ForeignKey('department.departmentID'))
    machineID = db.Column(db.String(255), db.ForeignKey('machinery.machineID'))
    kg_per_box = db.Column(db.Numeric(20, 3))
    kg_per_each = db.Column(db.Numeric(20, 3))
    units_per_box = db.Column(db.Integer)
    stock_item = db.Column(db.Boolean, default=True)
    min_stocks_in_boxes = db.Column(db.Integer)
    max_stocks_in_boxes = db.Column(db.Integer)
    fill_weight = db.Column(db.Numeric(20, 3))
    casing = db.Column(db.String(255))
    ideal_batch_size = db.Column(db.Integer)

    # Define relationships
    category = db.relationship('Category', backref='item_masters')
    department = db.relationship('Department', backref='item_masters')
    machine = db.relationship('Machinery', backref='item_masters')
    item_type = db.relationship('ItemType', backref='item_masters')

class RecipeMaster(db.Model):
    __tablename__ = 'recipe_master'
    
    # Primary composite key using finished product ID and raw material ID
    finished_product_id = db.Column(db.String(255), db.ForeignKey('item_master.itemID'), primary_key=True)
    raw_material_id = db.Column(db.String(255), db.ForeignKey('item_master.itemID'), primary_key=True)
    
    # Other fields
    recipeName = db.Column(db.String(255), nullable=False)
    usageMaterial = db.Column(db.Numeric(20, 3), nullable=False)
    uom = db.Column(db.String(50), nullable=False)
    percentage = db.Column(db.Numeric(5, 3))
    
    # Relationships
    finished_product = db.relationship('ItemMaster', foreign_keys=[finished_product_id], backref='recipes_as_product')
    raw_material = db.relationship('ItemMaster', foreign_keys=[raw_material_id], backref='recipes_as_material')

# class RecipeMaster(db.Model):
#     __tablename__ = 'recipe_master'
#     recipeID = db.Column(db.String(255), primary_key=True)
#     recipeName = db.Column(db.String(255), nullable=False)
#     itemID = db.Column(db.String(255), db.ForeignKey('item_master.itemID'), nullable=False)
#     rawMaterial = db.Column(db.String(255), nullable=False)
#     usageMaterial = db.Column(db.Numeric(20, 3), nullable=False)
#     uom = db.Column(db.String(50), nullable=False)
#     percentage = db.Column(db.Numeric(5, 3))


@app.route('/')
def index():
    categories = Category.query.all()
    return render_template('index.html')

@app.route('/item-master', methods=['GET', 'POST'])
def item_master():
    categories = Category.query.all()  # Fetch all categories
    departments = Department.query.all() #fetch all departments
    machines = Machinery.query.all() #fetch all machines
    types = ItemType.query.all() #fetch all item types
    items = ItemMaster.query.all() # Default: show all items

    if request.method == 'POST':
        selected_category_id = request.form.get('categoryID') #Get the selected category
        print(f"Selected Category ID: {selected_category_id}") #Check the selected category in the backend

        if selected_category_id:
            #Filter the items based on the selected category
            items = ItemMaster.query.filter_by(categoryID=selected_category_id).all()

        return render_template('item-master.html', items=items, categories=categories, departments=departments, machines=machines, types=types)
    else:
        return render_template('item-master.html', items=items, categories=categories, departments=departments, machines=machines, types=types)

# @app.route('/recipe-master')
# def recipe_master():
#     recipes = RecipeMaster.query.all()

#     #calculate percentage
#     percentages = {}
#     for recipe in recipes:
#         total_usage_for_name = db.session.query(db.func.sum(RecipeMaster.usageMaterial)).filter(RecipeMaster.recipeName == recipe.recipeName).scalar()

#         # Convert total_usage_for_name to float before division
#         total_usage_for_name = float(total_usage_for_name) if total_usage_for_name else 0.0

#         percentage = (float(recipe.usageMaterial) / total_usage_for_name) * 100 if total_usage_for_name else 0
#         percentages[recipe.recipeID] = percentage

#     return render_template('recipe-master.html', recipes=recipes, percentages=percentages)

# @app.route('/recipe-master', methods=['GET'])
# def recipe_master():
#     search_item_no = request.args.get('item_no', '')
#     search_name = request.args.get('name', '')

#     recipes = RecipeMaster.query

#     if search_item_no:
#          recipes = recipes.join(ItemMaster, RecipeMaster.finished_product_id == ItemMaster.itemID).filter(ItemMaster.itemID.ilike(f"%{search_item_no}%"))
#     if search_name:
#         recipes = recipes.filter(RecipeMaster.recipeName.ilike(f"%{search_name}%"))

#     recipes = recipes.all()

#     #calculate percentage
#     percentages = {}
#     for recipe in recipes:
#         #total_usage_for_name = db.session.query(db.func.sum(RecipeMaster.usageMaterial)).filter(RecipeMaster.recipeName == recipe.recipeName).scalar()
#         total_usage_subquery = db.session.query(func.sum(RecipeMaster.usageMaterial)).filter(RecipeMaster.recipeName == recipe.recipeName).subquery()
#         total_usage_for_name = db.session.query(total_usage_subquery).scalar()


#         # Convert total_usage_for_name to float before division
#         total_usage_for_name = float(total_usage_for_name) if total_usage_for_name else 0.0

#         percentage = (float(recipe.usageMaterial) / total_usage_for_name) * 100 if total_usage_for_name else 0
#         percentages[(recipe.finished_product_id, recipe.raw_material_id)] = percentage  # Use composite key as dictionary key
        
#         #percentages[recipe.recipeID] = percentage

#     return render_template('recipe_search.html', recipes=recipes, percentages=percentages, search_item_no=search_item_no, search_name=search_name)

@app.route('/recipe-master', methods=['GET'])
def recipe_master():
    search_item_no = request.args.get('item_no', '')
    search_name = request.args.get('name', '')

    # Query items instead of recipes
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

    # Get all reference data for dropdowns/display
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

@app.route('/recipe/add', methods=['GET', 'POST'])
def recipe_add():
    if request.method == 'POST':
        recipeID = request.form.get('recipeID')
        recipeName = request.form.get('recipeName')
        itemID = request.form.get('itemID')
        rawMaterial = request.form.get('rawMaterial')
        usageMaterial = request.form.get('usageMaterial')
        uom = request.form.get('uom')

        try:
            # Validate input
            if not all([recipeID, recipeName, itemID, rawMaterial, usageMaterial, uom]):
                flash("All fields are required.", 'error')
                return render_template('recipe_add.html')

            usageMaterial = Decimal(usageMaterial)  # Convert to Decimal

            # Calculate percentage
            total_usage_for_name = db.session.query(db.func.sum(RecipeMaster.usageMaterial)).filter(RecipeMaster.recipeName == recipeName).scalar()
            total_usage_for_name = float(total_usage_for_name) if total_usage_for_name else 0.0
            percentage = (float(usageMaterial) / total_usage_for_name) * 100 if total_usage_for_name else 0

            # Create new recipe
            new_recipe = RecipeMaster(
                recipeID=recipeID,
                recipeName=recipeName,
                itemID=itemID,
                rawMaterial=rawMaterial,
                usageMaterial=usageMaterial,
                uom=uom,
                percentage=Decimal(percentage)  # Store percentage as Decimal
            )

            db.session.add(new_recipe)
            db.session.commit()

            flash("Recipe added successfully!", 'success')
            #return redirect(url_for('recipe_master'))
            return redirect(url_for('recipe_add'))

        except ValueError:
            flash("Invalid input. Please check your data.", 'error')
            db.session.rollback()
            recipes = RecipeMaster.query.all()
            return render_template('recipe_add.html')

        except sqlalchemy.exc.IntegrityError as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", 'error')  # Display specific error
            recipes = RecipeMaster.query.all()
            return render_template('recipe_add.html')

        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred: {str(e)}", 'error')
            recipes = RecipeMaster.query.all()
            return render_template('recipe_add.html')
        
    recipes = RecipeMaster.query.all()
    return render_template('recipe_add.html')    

@app.route('/add_category', methods=['POST'])
def add_category():
    try:
        category_id = request.form['categoryID']
        category_name = request.form['categoryName']
        new_category = Category(categoryID=category_id, categoryName=category_name)
        db.session.add(new_category)
        db.session.commit()
        flash('Category added successfully!', 'success')
    except sqlalchemy.exc.IntegrityError:
        db.session.rollback()
        flash('Category ID already exists.', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding category: {e}', 'error')
    return redirect(url_for('item_master'))

@app.route('/add_department', methods=['POST'])
def add_department():
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

        # Set machineID to None if it's empty
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

        # Check if item exists before trying to add
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
            print(f"Duplicate ID: {duplicate_id}")
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
    current_recipe = {}  # Store data for the current recipe item

    for key, value in request.form.items():
        key_parts = key.split('-')  # Split the key to extract field name and index
        if len(key_parts) == 2:
            field_name, item_index = key_parts
            item_index = int(item_index)

            # If this is a new item index, start a new recipe item
            if not current_recipe or current_recipe.get('item_index', None)!= item_index:
                if current_recipe:
                    recipe_items.append(current_recipe)  # Append the previous recipe
                    print("print the current recipes................",current_recipe)
                current_recipe = {'item_index': item_index}  # Create a new recipe item

            # Assign the value to the correct field in the current recipe
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

    # Append the last recipe item
    if current_recipe:
        recipe_items.append(current_recipe)


    # Calculate percentages after adding all items
    percentages = {}
    for item in recipe_items:
        total_usage_for_name = sum(item['usageMaterial'] for item in recipe_items if item['recipeName'] == item['recipeName'])
        percentage = (item['usageMaterial'] / total_usage_for_name) * 100 if total_usage_for_name else 0
        percentages[item['recipeID']] = percentage

    # Add recipes to the database
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

        results = db.session.execute(query, {"search": search + "%"}).fetchall()

        # Convert results to JSON
        suggestions = [{"item_no": row[0], "item_name": row[1]} for row in results]

        return jsonify(suggestions)

    except Exception as e:
        print("Error fetching autocomplete suggestions:", e)
        return jsonify([])

@app.route('/get_search_items', methods=['GET'])
def get_search_items():
    search_item_no = request.args.get('item_no', '').strip()
    search_name = request.args.get('name', '').strip()

    items_query = ItemMaster.query

    if search_item_no:
        items_query = items_query.filter(ItemMaster.itemID.like(f"{search_item_no}%"))
    if search_name:
        items_query = items_query.filter(ItemMaster.itemName.ilike(f"%{search_name}%"))

    items = items_query.all()

    items_data = [
        {"itemID": item.itemID, "itemName": item.itemName, "itemDescription": item.itemDescription, "itemTypeID": item.itemTypeID, "categoryID": item.categoryID, "departmentID": item.departmentID, "machineID": item.machineID, "kg_per_box": item.kg_per_box, "kg_per_each": item.kg_per_each, "units_per_box": item.units_per_box, "stock_item": item.stock_item, "min_stocks_in_boxes": item.min_stocks_in_boxes, "max_stocks_in_boxes": item.max_stocks_in_boxes, "fill_weight": item.fill_weight, "casing": item.casing, "ideal_batch_size": item.ideal_batch_size}
        for item in items
    ]

    return jsonify(items_data)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
