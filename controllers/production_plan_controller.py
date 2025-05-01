from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime

# Create Blueprint
production_plan_bp = Blueprint('production_plan', __name__, template_folder='templates')

# Add a route for /production_plan to redirect to /production_plan_list
@production_plan_bp.route('/production_plan', methods=['GET'])
def production_plan():
    """
    Redirect /production_plan to /production_plan_list.
    """
    return redirect(url_for('production_plan.production_plan_list'))

# Existing routes
@production_plan_bp.route('/production_plan_list', methods=['GET'])
def production_plan_list():
    """
    Display a list of all Production Plans.
    """
    from app import db
    from models.production_plan import ProductionPlan

    try:
        plans = ProductionPlan.query.all()
        return render_template('production_plan/list.html', plans=plans)
    except Exception as e:
        flash(f"Error loading Production Plans: {str(e)}", "error")
        return render_template('production_plan/list.html', plans=[])

@production_plan_bp.route('/production_plan_create', methods=['GET', 'POST'])
def production_plan_create():
    """
    Create a new Production Plan.
    GET: Display the form to create a new Production Plan.
    POST: Process the form data and save the new Production Plan.
    """
    from app import db
    from models.production_plan import ProductionPlan
    from models.finished_goods import FinishedGoods
    from models.machinery import Machinery
    from models.operator import Operator
    from models.traceability_production import TraceabilityProduction
    from models.cooking_records import CookingRecord

    if request.method == 'POST':
        try:
            # Extract form data
            description_id = int(request.form['description_id'])
            batches = float(request.form['batches']) if request.form['batches'] else 0.0
            weight = float(request.form['weight']) if request.form['weight'] else 0.0
            actual = float(request.form['actual']) if request.form['actual'] else 0.0
            batch_number_id = int(request.form['batch_number_id'])
            production_date_str = request.form['production_date']
            machineID = int(request.form['machineID'])
            priority = float(request.form['priority']) if request.form['priority'] else 0.0
            status = request.form['status']
            comments = request.form['comments']
            operator_id = int(request.form['operator_id']) if request.form['operator_id'] else None
            signature = request.form['signature']
            room = request.form['room']
            traceability_production_id = int(request.form['traceability_production_id']) if request.form.get('traceability_production_id') else None
            raw_weight = float(request.form['raw_weight']) if request.form['raw_weight'] else 0.0
            actual_injected_weight = float(request.form['actual_injected_weight']) if request.form['actual_injected_weight'] else 0.0
            cooking_record_id = int(request.form['cooking_record_id']) if request.form.get('cooking_record_id') else None

            # Parse production_date
            production_date = datetime.strptime(production_date_str, '%Y-%m-%d').date()

            # Create new Production Plan
            new_plan = ProductionPlan(
                description_id=description_id,
                batches=batches,
                weight=weight,
                actual=actual,
                batch_number_id=batch_number_id,
                production_date=production_date,
                machineID=machineID,
                priority=priority,
                status=status,
                comments=comments,
                operator_id=operator_id,
                signature=signature,
                room=room,
                traceability_production_id=traceability_production_id,
                raw_weight=raw_weight,
                actual_injected_weight=actual_injected_weight,
                cooking_record_id=cooking_record_id
            )

            # Save to database
            db.session.add(new_plan)
            db.session.commit()
            flash("Production Plan created successfully!", "success")
            return redirect(url_for('production_plan.production_plan_list'))

        except ValueError as ve:
            db.session.rollback()
            flash(f"Invalid input: {str(ve)}", "error")
            return redirect(url_for('production_plan.production_plan_create'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating Production Plan: {str(e)}", "error")
            return redirect(url_for('production_plan.production_plan_create'))

    # GET request: Display the form
    try:
        finished_goods = FinishedGoods.query.all()
        machines = Machinery.query.all()
        operators = Operator.query.all()
        traceability_productions = TraceabilityProduction.query.all()
        cooking_records = CookingRecord.query.all()

        return render_template('production_plan/create.html',
                             finished_goods=finished_goods,
                             machines=machines,
                             operators=operators,
                             traceability_productions=traceability_productions,
                             cooking_records=cooking_records,
                             statuses=['Planned', 'In Progress', 'Completed'],
                             rooms=['Room A', 'Room B', 'Room C'])
    except Exception as e:
        flash(f"Error loading form data: {str(e)}", "error")
        return render_template('production_plan/create.html',
                             finished_goods=[],
                             machines=[],
                             operators=[],
                             traceability_productions=[],
                             cooking_records=[],
                             statuses=['Planned', 'In Progress', 'Completed'],
                             rooms=['Room A', 'Room B', 'Room C'])

@production_plan_bp.route('/production_plan_edit/<int:id>', methods=['GET', 'POST'])
def production_plan_edit(id):
    """
    Edit an existing Production Plan.
    GET: Display the form with the existing Production Plan data.
    POST: Update the Production Plan with the new data.
    """
    from app import db
    from models.production_plan import ProductionPlan
    from models.finished_goods import FinishedGoods
    from models.machinery import Machinery
    from models.operator import Operator
    from models.traceability_production import TraceabilityProduction
    from models.cooking_records import CookingRecord

    plan = ProductionPlan.query.get_or_404(id)

    if request.method == 'POST':
        try:
            # Update fields from form data
            plan.description_id = int(request.form['description_id'])
            plan.batches = float(request.form['batches']) if request.form['batches'] else 0.0
            plan.weight = float(request.form['weight']) if request.form['weight'] else 0.0
            plan.actual = float(request.form['actual']) if request.form['actual'] else 0.0
            plan.batch_number_id = int(request.form['batch_number_id'])
            production_date_str = request.form['production_date']
            plan.production_date = datetime.strptime(production_date_str, '%Y-%m-%d').date()
            plan.machineID = int(request.form['machineID'])
            plan.priority = float(request.form['priority']) if request.form['priority'] else 0.0
            plan.status = request.form['status']
            plan.comments = request.form['comments']
            plan.operator_id = int(request.form['operator_id']) if request.form['operator_id'] else None
            plan.signature = request.form['signature']
            plan.room = request.form['room']
            plan.traceability_production_id = int(request.form['traceability_production_id']) if request.form.get('traceability_production_id') else None
            plan.raw_weight = float(request.form['raw_weight']) if request.form['raw_weight'] else 0.0
            plan.actual_injected_weight = float(request.form['actual_injected_weight']) if request.form['actual_injected_weight'] else 0.0
            plan.cooking_record_id = int(request.form['cooking_record_id']) if request.form.get('cooking_record_id') else None

            # Save changes
            db.session.commit()
            flash("Production Plan updated successfully!", "success")
            return redirect(url_for('production_plan.production_plan_list'))

        except ValueError as ve:
            db.session.rollback()
            flash(f"Invalid input: {str(ve)}", "error")
            return redirect(url_for('production_plan.production_plan_edit', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating Production Plan: {str(e)}", "error")
            return redirect(url_for('production_plan.production_plan_edit', id=id))

    # GET request: Display the form with existing data
    try:
        finished_goods = FinishedGoods.query.all()
        machines = Machinery.query.all()
        operators = Operator.query.all()
        traceability_productions = TraceabilityProduction.query.all()
        cooking_records = CookingRecord.query.all()

        return render_template('production_plan/edit.html',
                             plan=plan,
                             finished_goods=finished_goods,
                             machines=machines,
                             operators=operators,
                             traceability_productions=traceability_productions,
                             cooking_records=cooking_records,
                             statuses=['Planned', 'In Progress', 'Completed'],
                             rooms=['Room A', 'Room B', 'Room C'])
    except Exception as e:
        flash(f"Error loading form data: {str(e)}", "error")
        return render_template('production_plan/edit.html',
                             plan=plan,
                             finished_goods=[],
                             machines=[],
                             operators=[],
                             traceability_productions=[],
                             cooking_records=[],
                             statuses=['Planned', 'In Progress', 'Completed'],
                             rooms=['Room A', 'Room B', 'Room C'])

@production_plan_bp.route('/production_plan_delete/<int:id>', methods=['POST'])
def production_plan_delete(id):
    """
    Delete a Production Plan.
    """
    from app import db
    from models.production_plan import ProductionPlan

    plan = ProductionPlan.query.get_or_404(id)

    try:
        db.session.delete(plan)
        db.session.commit()
        flash("Production Plan deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting Production Plan: {str(e)}", "error")

    return redirect(url_for('production_plan.production_plan_list'))