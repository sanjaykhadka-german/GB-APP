from database import db

class Department(db.Model):
    __tablename__ = 'department'
    departmentID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    departmentName = db.Column(db.String(50), nullable=False, unique=True)