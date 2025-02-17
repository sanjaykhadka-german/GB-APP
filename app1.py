from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:german@localhost/gbdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your-secret-key'  # Required for flash messages
db = SQLAlchemy(app)

# Keep your existing model definitions

def generate_id(prefix):
    return f"{prefix}-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4]}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/item-master')
def item_master():
    # Fetch all required data for the page
    items = db.session.query(
        ItemMaster,
        ItemType.itemTypeName,
        Category.categoryName,
        Department.departmentName,
        Machinery.machineryName
    ).outerjoin(ItemType).outerjoin(Category).outerjoin(Department).outerjoin(Machinery).all()
    
    item_types = ItemType.query.all()
    categories = Category.query.all()
    departments = Department.query.all()
    machines = Machinery.query.all()
    
    return render_template('item-master.html',
                         items=items,
                         item_types=item_types,
                         categories=categories,
                         departments=departments,
                         machines=machines)

@app.route('/add-item', methods=['POST'])
def add_item():
    try:
        new_item = ItemMaster(
            itemID=generate_id('ITEM'),
            itemName=request.form['itemName'],
            itemDescription=request.form['itemDescription'],
            itemTypeID=request.form['itemTypeID'],
            categoryID=request.form['categoryID'],
            departmentID=request.form['departmentID'],
            machineID=request.form.get('machineID'),
            kg_per_box=request.form.get('kg_per_box'),
            kg_per_each=request.form.get('kg_per_each'),
            units_per_box=request.form.get('units_per_box'),
            min_stocks_in_boxes=request.form.get('min_stocks_in_boxes'),
            max_stocks_in_boxes=request.form.get('max_stocks_in_boxes'),
            fill_weight=request.form.get('fill_weight'),
            casing=request.form.get('casing'),
            ideal_batch_size=request.form.get('ideal_batch_size')
        )
        db.session.add(new_item)
        db.session.commit()
        flash('Item added successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding item: {str(e)}', 'error')
    return redirect(url_for('item_master'))

@app.route('/add-item-type', methods=['POST'])
def add_item_type():
    try:
        new_type = ItemType(
            itemTypeID=generate_id('TYPE'),
            itemTypeName=request.form['itemTypeName']
        )
        db.session.add(new_type)
        db.session.commit()
        flash('Item type added successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding item type: {str(e)}', 'error')
    return redirect(url_for('item_master'))

@app.route('/add-category', methods=['POST'])
def add_category():
    try:
        new_category = Category(
            categoryID=generate_id('CAT'),
            categoryName=request.form['categoryName']
        )
        db.session.add(new_category)
        db.session.commit()
        flash('Category added successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding category: {str(e)}', 'error')
    return redirect(url_for('item_master'))

@app.route('/add-department', methods=['POST'])
def add_department():
    try:
        new_department = Department(
            departmentID=generate_id('DEPT'),
            departmentName=request.form['departmentName']
        )
        db.session.add(new_department)
        db.session.commit()
        flash('Department added successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding department: {str(e)}', 'error')
    return redirect(url_for('item_master'))

@app.route('/add-machine', methods=['POST'])
def add_machine():
    try:
        new_machine = Machinery(
            machineID=generate_id('MACH'),
            machineryName=request.form['machineryName']
        )
        db.session.add(new_machine)
        db.session.commit()
        flash('Machine added successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding machine: {str(e)}', 'error')
    return redirect(url_for('item_master'))

@app.route('/recipe-master')
def recipe_master():
    recipes = RecipeMaster.query.all()
    return render_template('recipe-master.html', recipes=recipes)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)