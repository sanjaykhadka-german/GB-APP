# from datetime import datetime
# from database import db

# class FinishedGoods(db.Model):
#     __tablename__ = 'finished_goods'
#     id = db.Column(db.Integer, primary_key=True)
#     item_number = db.Column(db.Text, nullable=False)
#     description = db.Column(db.Text, nullable=True)
#     status = db.Column(db.Enum('active', 'inactive', name='status_enum'), nullable=False, default='active')
#     pack_weight = db.Column(db.Numeric(precision=10, scale=2), nullable=True)
#     units_per_bag = db.Column(db.Integer, nullable=True)
#     pieces_per_unit = db.Column(db.Integer, nullable=True)
#     product_prepare = db.Column(db.Text, nullable=True)
#     kind_of_packing = db.Column(db.Text, nullable=True)
#     die_set_bags_size = db.Column(db.Text, nullable=True)
#     packaging_material_1_id = db.Column(db.Integer, db.ForeignKey('raw_material_report.id'))
#     packaging_material_2_id = db.Column(db.Integer, db.ForeignKey('raw_material_report.id'))
#     offset_in_days = db.Column(db.Integer, nullable=True)
#     label_type_id = db.Column(db.Integer, db.ForeignKey('raw_material_report.id'))
#     box_label_type_id = db.Column(db.Integer, db.ForeignKey('raw_material_report.id'))
#     label_picture = db.Column(db.LargeBinary, nullable=True)  # Store image as binary
#     product_picture = db.Column(db.LargeBinary, nullable=True)  # Store image as binary
#     inner_box_type_id = db.Column(db.Integer, db.ForeignKey('raw_material_report.id'))
#     pack_per_inner = db.Column(db.Integer, nullable=True)
#     box_type_id = db.Column(db.Integer, db.ForeignKey('raw_material_report.id'))
#     units_per_box = db.Column(db.Integer, nullable=True)
#     boxes_per_pallet = db.Column(db.Integer, nullable=True)
#     pallet_configuration = db.Column(db.Text, nullable=True)
#     machineID = db.Column(db.Integer, db.ForeignKey('machinery.machineID'))
#     machine_program = db.Column(db.Text, nullable=True)
#     rw = db.Column(db.Boolean, default=False)
#     fw = db.Column(db.Boolean, default=False)
#     slicer_dicer_program = db.Column(db.Text, nullable=True)
#     label_type_enum = db.Column(db.Enum('type1', 'type2', 'type3', name='label_type_enum'), nullable=True)
#     packs_per_cycle = db.Column(db.Integer, nullable=True)
#     cycles_per_min = db.Column(db.Integer, nullable=True)
#     packs_per_min = db.Column(db.Integer, nullable=True)
#     packs_per_hr = db.Column(db.Integer, nullable=True)
#     kg_per_hr = db.Column(db.Numeric(precision=10, scale=2), nullable=True)
#     barcode = db.Column(db.Text, nullable=True)
#     minimum_soh_in_units = db.Column(db.Integer, nullable=True)
#     operator_id = db.Column(db.Integer, db.ForeignKey('operator.id'))
#     signature = db.Column(db.LargeBinary, nullable=True)
#     timestamp = db.Column(db.DateTime, default=datetime.utcnow)
#     fill_weight_raw_in_gr = db.Column(db.Numeric(precision=10, scale=2), nullable=True)
#     target_weight_in_gr = db.Column(db.Numeric(precision=10, scale=2), nullable=True)
#     filling_length_in_mm = db.Column(db.Integer, nullable=True)
#     filling_diameter_in_mm = db.Column(db.Text, nullable=True)
#     casing_used_id = db.Column(db.Integer, db.ForeignKey('raw_material_report.id'))
#     clip_used_id = db.Column(db.Integer, db.ForeignKey('raw_material_report.id'))
#     clip_pressure = db.Column(db.Text, nullable=True)
#     filling_program_id = db.Column(db.Text, nullable=True)
#     cooking_program_id = db.Column(db.Integer, db.ForeignKey('cooking_program.id'))
#     department_id = db.Column(db.Integer, db.ForeignKey('department.department_id'))
#     allergens_id = db.Column(db.Integer, db.ForeignKey('allergen.allergens_id'))
#     total_recipe_weight = db.Column(db.Numeric(precision=10, scale=2), nullable=True)
#     uom = db.Column(db.Text, nullable=True)
#     staff_required_filling = db.Column(db.Integer, nullable=True)
#     staff_required_packing = db.Column(db.Integer, nullable=True)
#     target_weight_filled_per_hour = db.Column(db.Integer, nullable=True)

#     # Relationships
#     packaging_material_1 = db.relationship('RawMaterialReport', foreign_keys=[packaging_material_1_id])
#     packaging_material_2 = db.relationship('RawMaterialReport', foreign_keys=[packaging_material_2_id])
#     label_type = db.relationship('RawMaterialReport', foreign_keys=[label_type_id])
#     box_label_type = db.relationship('RawMaterialReport', foreign_keys=[box_label_type_id])
#     inner_box_type = db.relationship('RawMaterialReport', foreign_keys=[inner_box_type_id])
#     box_type = db.relationship('RawMaterialReport', foreign_keys=[box_type_id])
#     casing_used = db.relationship('RawMaterialReport', foreign_keys=[casing_used_id])
#     clip_used = db.relationship('RawMaterialReport', foreign_keys=[clip_used_id])
#     machine = db.relationship('Machinery', foreign_keys=[machineID])
#     operator = db.relationship('Operator', foreign_keys=[operator_id])
#     cooking_program = db.relationship('CookingProgram', foreign_keys=[cooking_program_id])
#     department = db.relationship('Department', foreign_keys=[department_id])
#     allergens = db.relationship('Allergen', foreign_keys=[allergens_id])