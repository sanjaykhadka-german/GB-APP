from datetime import datetime
from database import db

class CookingRecord(db.Model):
    __tablename__ = 'cooking_record'
    id = db.Column(db.Integer, primary_key=True)
    production_plan_id = db.Column(db.Integer, db.ForeignKey('production_plan.id'), nullable=False)
    batch_number = db.Column(db.Text, nullable=False)
    product_id = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_above_65c_time = db.Column(db.Time, nullable=True)
    end_above_65c_time = db.Column(db.Time, nullable=True)
    holding_time_minutes = db.Column(db.Time, nullable=True)
    cooling_start_52c_time = db.Column(db.Time, nullable=True)
    end_cooling_12c_time = db.Column(db.Time, nullable=True)
    cooling_time = db.Column(db.Time, nullable=True)
    data_logger = db.Column(db.String(255), nullable=True)  # Store file path or filename
    comments = db.Column(db.Text, nullable=True)
    operator_id = db.Column(db.Integer, db.ForeignKey('operator.id'), nullable=False)
    operator_signature = db.Column(db.LargeBinary, nullable=True)  # Store signature as binary (e.g., image or base64)
    verified_by = db.Column(db.String(100), nullable=True)
    verified_signature = db.Column(db.LargeBinary, nullable=True)  # Store signature as binary
    verified = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    # production_plan = db.relationship('ProductionPlan', backref=db.backref('cooking_records', lazy=True))
    # operator = db.relationship('Operator', backref=db.backref('cooking_records', lazy=True))