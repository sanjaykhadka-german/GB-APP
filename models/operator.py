from database import db


class Operator(db.Model):
    __tablename__ = 'operator'
    id = db.Column(db.String(50), primary_key=True)  # ID as text
    name = db.Column(db.Text, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.department_id'), nullable=False)
    mobile_number = db.Column(db.String(20), nullable=True)
    email = db.Column(db.Text, nullable=True)
    dob = db.Column(db.Date, nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.Enum('active', 'inactive', 'on_leave', name='operator_status_enum'), nullable=False, default='active')
    suburb = db.Column(db.Text, nullable=True)

    # Relationships
    department = db.relationship('Department', backref=db.backref('operators', lazy=True))