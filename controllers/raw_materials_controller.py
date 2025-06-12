from flask import Blueprint, render_template, request, jsonify, flash
from database import db
from models import RawMaterials

raw_materials_bp = Blueprint('raw_materials', __name__, template_folder='templates')

@raw_materials_bp.route('/raw-materials')
def raw_materials_page():
    materials = RawMaterials.query.order_by(RawMaterials.raw_material_code).all()
    return render_template('raw_materials/raw_materials.html', materials=materials, current_page='raw_materials')

@raw_materials_bp.route('/raw-materials/add', methods=['POST'])
def add_material():
    try:
        raw_material = request.form.get('raw_material')
        raw_material_code = request.form.get('raw_material_code')
        description = request.form.get('description')
        category_id = request.form.get('category_id')
        department_id = request.form.get('department_id')
        uom_id = request.form.get('uom_id')
        min_level = request.form.get('min_level')
        max_level = request.form.get('max_level')
        price_per_kg = request.form.get('price_per_kg')

        if not raw_material or not raw_material_code:
            return jsonify({'success': False, 'message': 'Raw material name and code are required'}), 400

        # Check if material code already exists
        existing_material = RawMaterials.query.filter_by(raw_material_code=raw_material_code).first()
        if existing_material:
            return jsonify({'success': False, 'message': 'Raw material code already exists'}), 400

        new_material = RawMaterials(
            raw_material_code=raw_material_code,
            raw_material=raw_material,
            description=description,
            category_id=category_id if category_id else None,
            department_id=department_id if department_id else None,
            uom_id=uom_id if uom_id else None,
            min_level=float(min_level) if min_level else None,
            max_level=float(max_level) if max_level else None,
            price_per_kg=float(price_per_kg) if price_per_kg else None
        )
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
        raw_material_code = request.form.get('raw_material_code')
        description = request.form.get('description')
        category_id = request.form.get('category_id')
        department_id = request.form.get('department_id')
        uom_id = request.form.get('uom_id')
        min_level = request.form.get('min_level')
        max_level = request.form.get('max_level')
        price_per_kg = request.form.get('price_per_kg')

        if not all([material_id, raw_material, raw_material_code]):
            return jsonify({'success': False, 'message': 'Material ID, name, and code are required'}), 400

        # Check if material exists
        material = RawMaterials.query.get(material_id)
        if not material:
            return jsonify({'success': False, 'message': 'Raw material not found'}), 404

        # Check if new code already exists for different material
        existing_material = RawMaterials.query.filter_by(raw_material_code=raw_material_code).first()
        if existing_material and existing_material.id != int(material_id):
            return jsonify({'success': False, 'message': 'Raw material code already exists'}), 400

        material.raw_material_code = raw_material_code
        material.raw_material = raw_material
        material.description = description
        material.category_id = category_id if category_id else None
        material.department_id = department_id if department_id else None
        material.uom_id = uom_id if uom_id else None
        material.min_level = float(min_level) if min_level else None
        material.max_level = float(max_level) if max_level else None
        material.price_per_kg = float(price_per_kg) if price_per_kg else None

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