# app.py
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy.orm import relationship
from sqlalchemy import String, Integer, DECIMAL, Boolean, Date, ForeignKey
from decimal import Decimal

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:german@localhost/gbdb'
db = SQLAlchemy(app)

# models here (ItemType, Category, Department, RawMaterialMaster, RecipeMaster, ItemMaster, SOH_Master, ProductionPlanMaster)

class ItemType(db.Model):
    __tablename__ = 'item_type'
    itemTypeID = db.Column(db.String(255), primary_key=True)
    itemTypeName = db.Column(db.String(50), nullable=False)

class Category(db.Model):
    __tablename__ = 'category'
    categoryID = db.Column(db.String(255), primary_key=True)
    categoryName = db.Column(db.String(50), nullable=False, unique=True)

    def __repr__(self):
        return f'<Category {self.name}>'

class Department(db.Model):
    __tablename__ = 'department'
    departmentID = db.Column(db.String(255), primary_key=True)
    departmentName = db.Column(db.String(50), nullable=False, unique=True)


class Machinery(db.Model):
    __tablename__ = 'machinery'
    machineID = db.Column(db.String(255), primary_key=True)
    machineryName = db.Column(db.String(50), nullable=False, unique=True)


class ItemMaster(db.Model):
    __tablename__ = 'item_master'
    itemID = db.Column(db.String(255), primary_key=True)
    itemName = db.Column(db.String(255), nullable=False)
    itemDescription = db.Column(db.String(255), nullable=False)
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

class RecipeMaster(db.Model):
    __tablename__ = 'recipe_master'
    recipeID = db.Column(db.String(255), primary_key=True)
    recipeName = db.Column(db.String(255), nullable=False)
    itemID = db.Column(db.String(255), db.ForeignKey('item_master.itemID'), nullable=False)
    rawMaterial = db.Column(db.String(255), nullable=False)
    usageMaterial = db.Column(db.Numeric(20, 3), nullable=False)
    uom = db.Column(db.String(50), nullable=False)
    percentage = db.Column(db.Numeric(5, 3))


@app.route('/')
def index():
    categories = Category.query.all()
    return render_template('index.html')

@app.route('/item-master', methods=['GET', 'POST'])
def item_master():
    #items = ItemMaster.query.all()
    categories = Category.query.all()  # Fetch all categories
    departments = Department.query.all() #fetch all departments
    machines = Machinery.query.all() #fetch all machines
    types = ItemType.query.all() #fetch all item types
    if request.method == 'POST':
        selected_category_id = request.form.get('categoryID') #Get the selected category
        print(f"Selected Category ID: {selected_category_id}") #Check the selected category in the backend

        if selected_category_id:
            #Filter the items based on the selected category
            items = ItemMaster.query.filter_by(categoryID=selected_category_id).all()
        else:
            #If no category is selected, show all items
            items = ItemMaster.query.all()

    else:
        items = ItemMaster.query.all()

    return render_template('item-master.html', items=items, categories=categories, departments=departments, machines=machines, types=types)
    
    

@app.route('/recipe-master')
def recipe_master():
    recipes = RecipeMaster.query.all()

    #calculate percentage
    percentages = {}
    for recipe in recipes:
        total_usage_for_name = db.session.query(db.func.sum(RecipeMaster.usageMaterial)).filter(RecipeMaster.recipeName == recipe.recipeName).scalar()
        
        # Convert total_usage_for_name to float before division
        total_usage_for_name = float(total_usage_for_name) if total_usage_for_name else 0.0

        percentage = (float(recipe.usageMaterial) / total_usage_for_name) * 100 if total_usage_for_name else 0
        percentages[recipe.recipeID] = percentage


    return render_template('recipe-master.html', recipes=recipes, percentages=percentages)



@app.route('/add_category', methods=['POST'])
def add_category():
    categoryID = request.form['categoryID']
    categoryName = request.form['categoryName']
    new_category = Category(categoryID=categoryID, categoryName=categoryName)
    db.session.add(new_category)
    db.session.commit()
    return redirect(url_for('item_master'))

@app.route('/add_department', methods=['POST'])
def add_department():
    departmentID = request.form['departmentID']
    departmentName = request.form['departmentName']
    new_department = Department(departmentID=departmentID, departmentName=departmentName)
    db.session.add(new_department)
    db.session.commit()
    return redirect(url_for('item_master'))

@app.route('/add_machine', methods=['POST'])
def add_machine():
    machineID = request.form['machineID']
    machineryName = request.form['machineryName']
    new_machine = Machinery(machineID=machineID, machineryName=machineryName)
    db.session.add(new_machine)
    db.session.commit()
    return redirect(url_for('item_master'))

@app.route('/add_item_type', methods=['POST'])
def add_item_type():
    itemTypeID = request.form['itemTypeID']
    itemTypeName = request.form['itemTypeName']
    new_item_type = ItemType(itemTypeID=itemTypeID, itemTypeName=itemTypeName)
    db.session.add(new_item_type)
    db.session.commit()
    return redirect(url_for('item_master'))


@app.route('/add_item', methods=['POST'])
def add_item():
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
    if machineID == '':
        machineID = None

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
    db.session.add(new_item)
    db.session.commit()
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
    return redirect(url_for('recipe_master'))





if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
