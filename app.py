# app.py
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy.orm import relationship
from sqlalchemy import String, Integer, DECIMAL, Boolean, Date, ForeignKey

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
    kg_per_box = db.Column(db.Numeric(10, 2))
    kg_per_each = db.Column(db.Numeric(10, 2))
    units_per_box = db.Column(db.Integer)
    stock_item = db.Column(db.Boolean, default=True)
    min_stocks_in_boxes = db.Column(db.Integer)
    max_stocks_in_boxes = db.Column(db.Integer)
    fill_weight = db.Column(db.Numeric(10, 2))
    casing = db.Column(db.String(255))
    ideal_batch_size = db.Column(db.Integer)

class RecipeMaster(db.Model):
    __tablename__ = 'recipe_master'
    recipeID = db.Column(db.String(255), primary_key=True)
    recipeName = db.Column(db.String(255), nullable=False)
    itemID = db.Column(db.String(255), db.ForeignKey('item_master.itemID'), nullable=False)
    usageMaterial = db.Column(db.Numeric(10, 2), nullable=False)
    uom = db.Column(db.String(50), nullable=False)
    percentage = db.Column(db.Numeric(5, 2), nullable=False)

# class SOH_Master(db.Model):
#     __tablename__ = 'SOH_Master'
#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     item_id = db.Column(db.Integer, ForeignKey('ItemMaster.id', ondelete='CASCADE'), nullable=False)
#     soh = db.Column(DECIMAL(10, 2), nullable=False)
#     uom = db.Column(db.String(50), nullable=False)
#     start_date = db.Column(Date, nullable=False)
#     week_commencing = db.Column(Date, nullable=False)
#     item = relationship("ItemMaster", back_populates="soh_entries")



# class ProductionPlanMaster(db.Model):
#     __tablename__ = 'ProductionPlanMaster'
#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     week_commencing = db.Column(Date, nullable=False)
#     start_date = db.Column(Date)
#     item_id = db.Column(db.Integer, ForeignKey('ItemMaster.id', ondelete='CASCADE'), nullable=False)
#     item_type = db.Column(db.String(255), nullable=False)
#     SOH = db.Column(db.Integer)
#     UOM = db.Column(db.String(50))
#     unit_produce_theoretical = db.Column(db.Integer)
#     kg_produce_theoretical = db.Column(db.Integer)
#     batches_theoretical = db.Column(db.Integer)
#     actual_batches_to_produce = db.Column(db.Integer)
#     adjustment_column_kg = db.Column(DECIMAL(10, 2))
#     kg_to_produce = db.Column(DECIMAL(10, 2))
#     units_to_produce = db.Column(db.Integer)
#     item = relationship("ItemMaster", back_populates="production_plans")


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/item-master')
def item_master():
    items = ItemMaster.query.all()
    return render_template('item-master.html', items=items)

@app.route('/recipe-master')
def recipe_master():
    recipes = RecipeMaster.query.all()
    return render_template('recipe-master.html', recipes=recipes)

# @app.route('/production-plan')
# def production_plan():
#     plans = ProductionPlanMaster.query.all()
#     return render_template('production-plan.html', plans=plans)


# @app.route('/soh')
# def soh():
#     if request.method == 'POST':
#         # Handle form submission
#         new_soh = SOH_Master(
#             item_id=request.form['item_id'],
#             soh=float(request.form['soh']),
#             uom=request.form['uom'],
#             start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date(),
#             week_commencing=datetime.strptime(request.form['week_commencing'], '%Y-%m-%d').date()
#         )
#         db.session.add(new_soh)
#         db.session.commit()
#         return redirect(url_for('soh'))

#     # GET request: display SOH items
#     soh_items = SOH_Master.query.all()
#     return render_template('soh.html', soh_items=soh_items)

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
    recipeID = request.form['recipeID']
    recipeName = request.form['recipeName']
    itemID = request.form['itemID']
    usageMaterial = request.form['usageMaterial']
    uom = request.form['uom']
    percentage = request.form['percentage']

    new_recipe = RecipeMaster(
        recipeID=recipeID,
        recipeName=recipeName,
        itemID=itemID,
        usageMaterial=usageMaterial,
        uom=uom,
        percentage=percentage
    )
    db.session.add(new_recipe)
    db.session.commit()
    return redirect(url_for('recipe_master'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
