from flask import Blueprint
from flask import flash, request, redirect, url_for
from models import Category
from database import db
import sqlalchemy

category_bp = Blueprint('category', __name__)

@category_bp.route('/add_category', methods=['POST'])
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