from database import db
from datetime import date



class CookingProgram(db.Model):
    __tablename__ = 'cooking_program'
    id = db.Column(db.Integer, primary_key=True)
    program_number = db.Column(db.String(50), nullable=False)
    program_name = db.Column(db.Text, nullable=False)
    operator_id = db.Column(db.Integer, db.ForeignKey('operator.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    signature = db.Column(db.LargeBinary, nullable=True)  # Store signature as binary (e.g., image or base64)

    # Relationships
    operator = db.relationship('Operator', backref=db.backref('cooking_programs', lazy=True))