from flask import Blueprint
from flask import flash, request, redirect, url_for
from models import Department
from database import db
import sqlalchemy

department_bp = Blueprint('department', __name__)


@department_bp.route('/add_department', methods=['POST'])
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