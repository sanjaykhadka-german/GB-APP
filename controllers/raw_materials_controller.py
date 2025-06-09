from flask import Blueprint, render_template, request, jsonify, flash
from database import db
from models import RawMaterials

raw_materials_bp = Blueprint('raw_materials', __name__, template_folder='templates')

@raw_materials_bp.route('/raw-materials')
def raw_materials_page():
    materials = RawMaterials.query.order_by(RawMaterials.raw_material).all()
    return render_template('raw_materials/raw_materials.html', materials=materials, current_page='raw_materials')

@raw_materials_bp.route('/raw-materials/add', methods=['POST'])
def add_material():
    try:
        raw_material = request.form.get('raw_material')
        if not raw_material:
            return jsonify({'success': False, 'message': 'Raw material name is required'}), 400

        # Check if material already exists
        existing_material = RawMaterials.query.filter_by(raw_material=raw_material).first()
        if existing_material:
            return jsonify({'success': False, 'message': 'Raw material already exists'}), 400

        new_material = RawMaterials(raw_material=raw_material)
        db.session.add(new_material)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Raw material added successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@raw_materials_bp.route('/raw-materials/edit', methods=['POST'])
def edit_material():
    try:
        material_id = request.form.get('material_id')
        raw_material = request.form.get('raw_material')

        if not all([material_id, raw_material]):
            return jsonify({'success': False, 'message': 'All fields are required'}), 400

        # Check if material exists
        material = RawMaterials.query.get(material_id)
        if not material:
            return jsonify({'success': False, 'message': 'Raw material not found'}), 404

        # Check if new name already exists for different material
        existing_material = RawMaterials.query.filter_by(raw_material=raw_material).first()
        if existing_material and existing_material.id != int(material_id):
            return jsonify({'success': False, 'message': 'Raw material name already exists'}), 400

        material.raw_material = raw_material
        db.session.commit()

        return jsonify({'success': True, 'message': 'Raw material updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@raw_materials_bp.route('/raw-materials/delete/<int:id>', methods=['POST'])
def delete_material(id):
    try:
        material = RawMaterials.query.get(id)
        if not material:
            return jsonify({'success': False, 'message': 'Raw material not found'}), 404

        # Check if material is being used in recipes
        if hasattr(material, 'recipes') and material.recipes:
            return jsonify({
                'success': False, 
                'message': 'Cannot delete raw material as it is being used in recipes'
            }), 400

        db.session.delete(material)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Raw material deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500 