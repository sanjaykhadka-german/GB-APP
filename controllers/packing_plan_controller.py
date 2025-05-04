from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
import os
from werkzeug.utils import secure_filename

# Create Blueprint
packing_plan_bp = Blueprint('packing_plan', __name__, template_folder='templates')

# your routes here


# File upload configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes for PackingPlan
@packing_plan_bp.route('/packing_plan', methods=['GET'])
def packing_plan():
    """
    Redirect /packing_plan to /packing_plan_list.
    """
    return redirect(url_for('packing_plan.packing_plan_list'))

@packing_plan_bp.route('/packing_plan_list', methods=['GET'])
def packing_plan_list():
    """
    Display a list of all Packing Plans.
    """
    from app import db
    from models.packing_plan import PackingPlan

    try:
        plans = PackingPlan.query.all()
        return render_template('packing_plan/list.html', plans=plans)
    except Exception as e:
        flash(f"Error loading Packing Plans: {str(e)}", "error")
        return render_template('packing_plan/list.html', plans=[])

@packing_plan_bp.route('/packing_plan_create', methods=['GET', 'POST'])
def packing_plan_create():
    """
    Create a new Packing Plan.
    GET: Display the form to create a new Packing Plan.
    POST: Process the form data and save the new Packing Plan.
    """
    from app import db
    from models.packing_plan import PackingPlan
    from models.week_commencing import WeekCommencing
    from models.finished_goods import FinishedGoods
    from models.batch_coding import BatchCoding
    from models.machinery import Machinery
    from models.operator import Operator
    from models.film_waste import FilmWaste
    from models.metal_detection import MetalDetection

    if request.method == 'POST':
        try:
            # Handle file uploads
            temperature_picture = None
            label_picture = None

            if 'temperature_picture' in request.files:
                file = request.files['temperature_picture']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(file_path)
                    temperature_picture = file_path

            if 'label_picture' in request.files:
                file = request.files['label_picture']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(file_path)
                    label_picture = file_path

            # Extract form data
            id = request.form['id']
            week_commencing_id = int(request.form['week_commencing_id'])
            date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            description_id = int(request.form['description_id'])
            pasteurisation = 'pasteurisation' in request.form
            pasteurisation_status = request.form['pasteurisation_status'] if request.form['pasteurisation_status'] else None
            kg_planned = float(request.form['kg_planned']) if request.form['kg_planned'] else 0.0
            units_planned = int(request.form['units_planned']) if request.form['units_planned'] else 0
            units_packed = int(request.form['units_packed']) if request.form['units_packed'] else 0
            wastage = float(request.form['wastage']) if request.form['wastage'] else 0.0
            boxes = float(request.form['boxes']) if request.form['boxes'] else 0.0
            inner_box_id = int(request.form['inner_box_id']) if request.form['inner_box_id'] else None
            pack_per_inner = int(request.form['pack_per_inner']) if request.form['pack_per_inner'] else 0
            inner_boxes_needed = int(request.form['inner_boxes_needed']) if request.form['inner_boxes_needed'] else 0
            inner_label_id = int(request.form['inner_label_id']) if request.form['inner_label_id'] else None
            outer_box_id = int(request.form['outer_box_id']) if request.form['outer_box_id'] else None
            inner_per_outer = int(request.form['inner_per_outer']) if request.form['inner_per_outer'] else 0
            outer_boxes_needed = int(request.form['outer_boxes_needed']) if request.form['outer_boxes_needed'] else 0
            outer_label_id = int(request.form['outer_label_id']) if request.form['outer_label_id'] else None
            batch_number_id = int(request.form['batch_number_id'])
            machine_id = int(request.form['machine_id'])
            priority = float(request.form['priority']) if request.form['priority'] else 0.0
            kg_packed = float(request.form['kg_packed']) if request.form['kg_packed'] else 0.0
            temperature = float(request.form['temperature']) if request.form['temperature'] else 0.0
            offset = int(request.form['offset']) if request.form['offset'] else 0
            use_by_date = datetime.strptime(request.form['use_by_date'], '%Y-%m-%d').date() if request.form['use_by_date'] else None
            packaging_material_1_id = int(request.form['packaging_material_1_id']) if request.form['packaging_material_1_id'] else None
            pm1_batch_number = request.form['pm1_batch_number'] if request.form['pm1_batch_number'] else None
            bw_needed = float(request.form['bw_needed']) if request.form['bw_needed'] else 0.0
            packaging_material_2_id = int(request.form['packaging_material_2_id']) if request.form['packaging_material_2_id'] else None
            pm2_batch_number = request.form['pm2_batch_number'] if request.form['pm2_batch_number'] else None
            tw_needed = float(request.form['tw_needed']) if request.form['tw_needed'] else 0.0
            film_waste_id = int(request.form['film_waste_id']) if request.form['film_waste_id'] else None
            film_waste_units = int(request.form['film_waste_units']) if request.form['film_waste_units'] else 0
            comments = request.form['comments'] if request.form['comments'] else None
            status = request.form['status'] if request.form['status'] else 'Planned'
            operator_id = int(request.form['operator_id']) if request.form['operator_id'] else None
            signature = request.form['signature'] if request.form['signature'] else None
            metal_detection_id = int(request.form['metal_detection_id']) if request.form['metal_detection_id'] else None
            start_time = datetime.strptime(request.form['start_time'], '%H:%M').time() if request.form['start_time'] else None
            finish_time = datetime.strptime(request.form['finish_time'], '%H:%M').time() if request.form['finish_time'] else None
            packing_date = datetime.strptime(request.form['packing_date'], '%Y-%m-%d').date() if request.form['packing_date'] else None
            units_packed_per_hour = float(request.form['units_packed_per_hour']) if request.form['units_packed_per_hour'] else 0.0
            units_target_per_hour = float(request.form['units_target_per_hour']) if request.form['units_target_per_hour'] else 0.0
            kg_packed_per_hour = float(request.form['kg_packed_per_hour']) if request.form['kg_packed_per_hour'] else 0.0
            kg_target_per_hour = float(request.form['kg_target_per_hour']) if request.form['kg_target_per_hour'] else 0.0
            timestamp = datetime.strptime(request.form['timestamp'], '%H:%M').time() if request.form['timestamp'] else None
            hrs_to_produce = float(request.form['hrs_to_produce']) if request.form['hrs_to_produce'] else 0.0
            staff_allocated_id = int(request.form['staff_allocated_id']) if request.form['staff_allocated_id'] else None
            staff_count = int(request.form['staff_count']) if request.form['staff_count'] else 0
            retention_samples = 'retention_samples' in request.form

            # Create new Packing Plan
            new_plan = PackingPlan(
                id=id,
                week_commencing_id=week_commencing_id,
                date=date,
                description_id=description_id,
                pasteurisation=pasteurisation,
                pasteurisation_status=pasteurisation_status,
                kg_planned=kg_planned,
                units_planned=units_planned,
                units_packed=units_packed,
                wastage=wastage,
                boxes=boxes,
                inner_box_id=inner_box_id,
                pack_per_inner=pack_per_inner,
                inner_boxes_needed=inner_boxes_needed,
                inner_label_id=inner_label_id,
                outer_box_id=outer_box_id,
                inner_per_outer=inner_per_outer,
                outer_boxes_needed=outer_boxes_needed,
                outer_label_id=outer_label_id,
                batch_number_id=batch_number_id,
                machine_id=machine_id,
                priority=priority,
                kg_packed=kg_packed,
                temperature_picture=temperature_picture,
                temperature=temperature,
                label_picture=label_picture,
                offset=offset,
                use_by_date=use_by_date,
                packaging_material_1_id=packaging_material_1_id,
                pm1_batch_number=pm1_batch_number,
                bw_needed=bw_needed,
                packaging_material_2_id=packaging_material_2_id,
                pm2_batch_number=pm2_batch_number,
                tw_needed=tw_needed,
                film_waste_id=film_waste_id,
                film_waste_units=film_waste_units,
                comments=comments,
                status=status,
                operator_id=operator_id,
                signature=signature,
                metal_detection_id=metal_detection_id,
                start_time=start_time,
                finish_time=finish_time,
                packing_date=packing_date,
                units_packed_per_hour=units_packed_per_hour,
                units_target_per_hour=units_target_per_hour,
                kg_packed_per_hour=kg_packed_per_hour,
                kg_target_per_hour=kg_target_per_hour,
                timestamp=timestamp,
                hrs_to_produce=hrs_to_produce,
                staff_allocated_id=staff_allocated_id,
                staff_count=staff_count,
                retention_samples=retention_samples
            )

            # Save to database
            db.session.add(new_plan)
            db.session.commit()
            flash("Packing Plan created successfully!", "success")
            return redirect(url_for('packing_plan.packing_plan_list'))

        except ValueError as ve:
            db.session.rollback()
            flash(f"Invalid input: {str(ve)}", "error")
            return redirect(url_for('packing_plan.packing_plan_create'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating Packing Plan: {str(e)}", "error")
            return redirect(url_for('packing_plan.packing_plan_create'))

    # GET request: Display the form
    try:
        week_commencings = WeekCommencing.query.all()
        finished_goods = FinishedGoods.query.all()
        batch_codings = BatchCoding.query.all()
        machines = Machinery.query.all()
        operators = Operator.query.all()
        film_wastes = FilmWaste.query.all()
        metal_detections = MetalDetection.query.all()

        return render_template('packing_plan/create.html',
                             week_commencings=week_commencings,
                             finished_goods=finished_goods,
                             batch_codings=batch_codings,
                             machines=machines,
                             operators=operators,
                             film_wastes=film_wastes,
                             metal_detections=metal_detections,
                             pasteurisation_statuses=['In Progress', 'Completed'],
                             statuses=['Planned', 'In Progress', 'Completed'])
    except Exception as e:
        flash(f"Error loading form data: {str(e)}", "error")
        return render_template('packing_plan/create.html',
                             week_commencings=[],
                             finished_goods=[],
                             batch_codings=[],
                             machines=[],
                             operators=[],
                             film_wastes=[],
                             metal_detections=[],
                             pasteurisation_statuses=['In Progress', 'Completed'],
                             statuses=['Planned', 'In Progress', 'Completed'])

@packing_plan_bp.route('/packing_plan_edit/<string:id>', methods=['GET', 'POST'])
def packing_plan_edit(id):
    """
    Edit an existing Packing Plan.
    GET: Display the form with the existing Packing Plan data.
    POST: Update the Packing Plan with the new data.
    """
    from app import db
    from models.packing_plan import PackingPlan
    from models.week_commencing import WeekCommencing
    from models.finished_goods import FinishedGoods
    from models.batch_coding import BatchCoding
    from models.machinery import Machinery
    from models.operator import Operator
    from models.film_waste import FilmWaste
    from models.metal_detection import MetalDetection

    plan = PackingPlan.query.get_or_404(id)

    if request.method == 'POST':
        try:
            # Handle file uploads
            if 'temperature_picture' in request.files:
                file = request.files['temperature_picture']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(file_path)
                    plan.temperature_picture = file_path

            if 'label_picture' in request.files:
                file = request.files['label_picture']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(file_path)
                    plan.label_picture = file_path

            # Update fields from form data
            plan.week_commencing_id = int(request.form['week_commencing_id'])
            plan.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            plan.description_id = int(request.form['description_id'])
            plan.pasteurisation = 'pasteurisation' in request.form
            plan.pasteurisation_status = request.form['pasteurisation_status'] if request.form['pasteurisation_status'] else None
            plan.kg_planned = float(request.form['kg_planned']) if request.form['kg_planned'] else 0.0
            plan.units_planned = int(request.form['units_planned']) if request.form['units_planned'] else 0
            plan.units_packed = int(request.form['units_packed']) if request.form['units_packed'] else 0
            plan.wastage = float(request.form['wastage']) if request.form['wastage'] else 0.0
            plan.boxes = float(request.form['boxes']) if request.form['boxes'] else 0.0
            plan.inner_box_id = int(request.form['inner_box_id']) if request.form['inner_box_id'] else None
            plan.pack_per_inner = int(request.form['pack_per_inner']) if request.form['pack_per_inner'] else 0
            plan.inner_boxes_needed = int(request.form['inner_boxes_needed']) if request.form['inner_boxes_needed'] else 0
            plan.inner_label_id = int(request.form['inner_label_id']) if request.form['inner_label_id'] else None
            plan.outer_box_id = int(request.form['outer_box_id']) if request.form['outer_box_id'] else None
            plan.inner_per_outer = int(request.form['inner_per_outer']) if request.form['inner_per_outer'] else 0
            plan.outer_boxes_needed = int(request.form['outer_boxes_needed']) if request.form['outer_boxes_needed'] else 0
            plan.outer_label_id = int(request.form['outer_label_id']) if request.form['outer_label_id'] else None
            plan.batch_number_id = int(request.form['batch_number_id'])
            plan.machine_id = int(request.form['machine_id'])
            plan.priority = float(request.form['priority']) if request.form['priority'] else 0.0
            plan.kg_packed = float(request.form['kg_packed']) if request.form['kg_packed'] else 0.0
            plan.temperature = float(request.form['temperature']) if request.form['temperature'] else 0.0
            plan.offset = int(request.form['offset']) if request.form['offset'] else 0
            plan.use_by_date = datetime.strptime(request.form['use_by_date'], '%Y-%m-%d').date() if request.form['use_by_date'] else None
            plan.packaging_material_1_id = int(request.form['packaging_material_1_id']) if request.form['packaging_material_1_id'] else None
            plan.pm1_batch_number = request.form['pm1_batch_number'] if request.form['pm1_batch_number'] else None
            plan.bw_needed = float(request.form['bw_needed']) if request.form['bw_needed'] else 0.0
            plan.packaging_material_2_id = int(request.form['packaging_material_2_id']) if request.form['packaging_material_2_id'] else None
            plan.pm2_batch_number = request.form['pm2_batch_number'] if request.form['pm2_batch_number'] else None
            plan.tw_needed = float(request.form['tw_needed']) if request.form['tw_needed'] else 0.0
            plan.film_waste_id = int(request.form['film_waste_id']) if request.form['film_waste_id'] else None
            plan.film_waste_units = int(request.form['film_waste_units']) if request.form['film_waste_units'] else 0
            plan.comments = request.form['comments'] if request.form['comments'] else None
            plan.status = request.form['status'] if request.form['status'] else 'Planned'
            plan.operator_id = int(request.form['operator_id']) if request.form['operator_id'] else None
            plan.signature = request.form['signature'] if request.form['signature'] else None
            plan.metal_detection_id = int(request.form['metal_detection_id']) if request.form['metal_detection_id'] else None
            plan.start_time = datetime.strptime(request.form['start_time'], '%H:%M').time() if request.form['start_time'] else None
            plan.finish_time = datetime.strptime(request.form['finish_time'], '%H:%M').time() if request.form['finish_time'] else None
            plan.packing_date = datetime.strptime(request.form['packing_date'], '%Y-%m-%d').date() if request.form['packing_date'] else None
            plan.units_packed_per_hour = float(request.form['units_packed_per_hour']) if request.form['units_packed_per_hour'] else 0.0
            plan.units_target_per_hour = float(request.form['units_target_per_hour']) if request.form['units_target_per_hour'] else 0.0
            plan.kg_packed_per_hour = float(request.form['kg_packed_per_hour']) if request.form['kg_packed_per_hour'] else 0.0
            plan.kg_target_per_hour = float(request.form['kg_target_per_hour']) if request.form['kg_target_per_hour'] else 0.0
            plan.timestamp = datetime.strptime(request.form['timestamp'], '%H:%M').time() if request.form['timestamp'] else None
            plan.hrs_to_produce = float(request.form['hrs_to_produce']) if request.form['hrs_to_produce'] else 0.0
            plan.staff_allocated_id = int(request.form['staff_allocated_id']) if request.form['staff_allocated_id'] else None
            plan.staff_count = int(request.form['staff_count']) if request.form['staff_count'] else 0
            plan.retention_samples = 'retention_samples' in request.form

            # Save changes
            db.session.commit()
            flash("Packing Plan updated successfully!", "success")
            return redirect(url_for('packing_plan.packing_plan_list'))

        except ValueError as ve:
            db.session.rollback()
            flash(f"Invalid input: {str(ve)}", "error")
            return redirect(url_for('packing_plan.packing_plan_edit', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating Packing Plan: {str(e)}", "error")
            return redirect(url_for('packing_plan.packing_plan_edit', id=id))

    # GET request: Display the form with existing data
    try:
        week_commencings = WeekCommencing.query.all()
        finished_goods = FinishedGoods.query.all()
        batch_codings = BatchCoding.query.all()
        machines = Machinery.query.all()
        operators = Operator.query.all()
        film_wastes = FilmWaste.query.all()
        metal_detections = MetalDetection.query.all()

        return render_template('packing_plan/edit.html',
                             plan=plan,
                             week_commencings=week_commencings,
                             finished_goods=finished_goods,
                             batch_codings=batch_codings,
                             machines=machines,
                             operators=operators,
                             film_wastes=film_wastes,
                             metal_detections=metal_detections,
                             pasteurisation_statuses=['In Progress', 'Completed'],
                             statuses=['Planned', 'In Progress', 'Completed'])
    except Exception as e:
        flash(f"Error loading form data: {str(e)}", "error")
        return render_template('packing_plan/edit.html',
                             plan=plan,
                             week_commencings=[],
                             finished_goods=[],
                             batch_codings=[],
                             machines=[],
                             operators=[],
                             film_wastes=[],
                             metal_detections=[],
                             pasteurisation_statuses=['In Progress', 'Completed'],
                             statuses=['Planned', 'In Progress', 'Completed'])

@packing_plan_bp.route('/packing_plan_delete/<string:id>', methods=['POST'])
def packing_plan_delete(id):
    """
    Delete a Packing Plan.
    """
    from app import db
    from models.packing_plan import PackingPlan

    plan = PackingPlan.query.get_or_404(id)

    try:
        db.session.delete(plan)
        db.session.commit()
        flash("Packing Plan deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting Packing Plan: {str(e)}", "error")

    return redirect(url_for('packing_plan.packing_plan_list'))