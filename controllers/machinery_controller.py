from flask import Blueprint
from flask import flash, request, redirect, url_for
from models import Machinery
from database import db
import sqlalchemy

machinery_bp = Blueprint('machinery', __name__)

@machinery_bp.route('/add_machine', methods=['POST'])        
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
