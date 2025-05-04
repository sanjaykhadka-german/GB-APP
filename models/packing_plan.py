from database import db
from datetime import date, time

class PackingPlan(db.Model):
    __tablename__ = 'packing_plan'

    # Primary key
    id = db.Column(db.String(50), primary_key=True)  # ID as text

    # Foreign keys and core fields
    week_commencing_id = db.Column(db.Integer, db.ForeignKey('week_commencing.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    description_id = db.Column(db.Integer, db.ForeignKey('finished_goods.id'), nullable=False)
    pasteurisation = db.Column(db.Boolean, default=False)
    pasteurisation_status = db.Column(db.Enum('In Progress', 'Completed'), nullable=True)
    kg_planned = db.Column(db.Float, default=0.0)
    units_planned = db.Column(db.Integer, default=0)
    units_packed = db.Column(db.Integer, default=0)
    wastage = db.Column(db.Numeric(precision=10, scale=2), default=0.0)
    boxes = db.Column(db.Numeric(precision=10, scale=2), default=0.0)
    inner_box_id = db.Column(db.Integer, db.ForeignKey('finished_goods.id'), nullable=True)
    pack_per_inner = db.Column(db.Integer, default=0)
    inner_boxes_needed = db.Column(db.Integer, default=0)
    inner_label_id = db.Column(db.Integer, db.ForeignKey('finished_goods.id'), nullable=True)
    outer_box_id = db.Column(db.Integer, db.ForeignKey('finished_goods.id'), nullable=True)
    inner_per_outer = db.Column(db.Integer, default=0)
    outer_boxes_needed = db.Column(db.Integer, default=0)
    outer_label_id = db.Column(db.Integer, db.ForeignKey('finished_goods.id'), nullable=True)
    batch_number_id = db.Column(db.Integer, db.ForeignKey('batch_coding.id'), nullable=False)
    machine_id = db.Column(db.Integer, db.ForeignKey('machinery.machineID'), nullable=False)
    priority = db.Column(db.Float, default=0.0)
    kg_packed = db.Column(db.Float, default=0.0)
    temperature_picture = db.Column(db.String(255), nullable=True)  # File path or URL for image
    temperature = db.Column(db.Numeric(precision=10, scale=2), default=0.0)
    label_picture = db.Column(db.String(255), nullable=True)  # File path or URL for image
    offset = db.Column(db.Integer, default=0)
    use_by_date = db.Column(db.Date, nullable=True)
    packaging_material_1_id = db.Column(db.Integer, db.ForeignKey('finished_goods.id'), nullable=True)
    pm1_batch_number = db.Column(db.String(50), nullable=True)
    bw_needed = db.Column(db.Numeric(precision=10, scale=2), default=0.0)
    packaging_material_2_id = db.Column(db.Integer, db.ForeignKey('finished_goods.id'), nullable=True)
    pm2_batch_number = db.Column(db.String(50), nullable=True)
    tw_needed = db.Column(db.Numeric(precision=10, scale=2), default=0.0)
    film_waste_id = db.Column(db.Integer, db.ForeignKey('film_waste.id'), nullable=True)
    film_waste_units = db.Column(db.Integer, default=0)
    comments = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='Planned')
    operator_id = db.Column(db.Integer, db.ForeignKey('operator.id'), nullable=True)
    signature = db.Column(db.String(255), nullable=True)  # Store signature as text (e.g., file path or name)
    metal_detection_id = db.Column(db.Integer, db.ForeignKey('metal_detection.id'), nullable=True)
    start_time = db.Column(db.Time, nullable=True)
    finish_time = db.Column(db.Time, nullable=True)
    packing_date = db.Column(db.Date, nullable=True)
    units_packed_per_hour = db.Column(db.Float, default=0.0)
    units_target_per_hour = db.Column(db.Float, default=0.0)
    kg_packed_per_hour = db.Column(db.Float, default=0.0)
    kg_target_per_hour = db.Column(db.Float, default=0.0)
    timestamp = db.Column(db.Time, nullable=True)
    hrs_to_produce = db.Column(db.Numeric(precision=10, scale=2), default=0.0)
    staff_allocated_id = db.Column(db.Integer, db.ForeignKey('operator.id'), nullable=True)
    staff_count = db.Column(db.Integer, default=0)
    retention_samples = db.Column(db.Boolean, default=False)

    # Relationships
    week_commencing = db.relationship('WeekCommencing', backref='packing_plans', foreign_keys=[week_commencing_id])
    description = db.relationship('FinishedGoods', backref='packing_plans_description', foreign_keys=[description_id])
    inner_box = db.relationship('FinishedGoods', backref='packing_plans_inner_box', foreign_keys=[inner_box_id])
    inner_label = db.relationship('FinishedGoods', backref='packing_plans_inner_label', foreign_keys=[inner_label_id])
    outer_box = db.relationship('FinishedGoods', backref='packing_plans_outer_box', foreign_keys=[outer_box_id])
    outer_label = db.relationship('FinishedGoods', backref='packing_plans_outer_label', foreign_keys=[outer_label_id])
    packaging_material_1 = db.relationship('FinishedGoods', backref='packing_plans_pm1', foreign_keys=[packaging_material_1_id])
    packaging_material_2 = db.relationship('FinishedGoods', backref='packing_plans_pm2', foreign_keys=[packaging_material_2_id])
    batch_number = db.relationship('BatchCoding', backref='packing_plans')
    machine = db.relationship('Machinery', backref='packing_plans')
    operator = db.relationship('Operator', backref='packing_plans_operator', foreign_keys=[operator_id])
    staff_allocated = db.relationship('Operator', backref='packing_plans_staff', foreign_keys=[staff_allocated_id])
    film_waste = db.relationship('FilmWaste', backref='packing_plans')
    metal_detection = db.relationship('MetalDetection', backref='packing_plans')

    def __repr__(self):
        return f"<PackingPlan {self.id}>"