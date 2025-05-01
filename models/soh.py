from database import db

class SOH(db.Model):
    __tablename__ = 'soh'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fg_code = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    soh_total_boxes = db.Column(db.Float, default=0.0)  # Store SOH Total Box
    soh_total_units = db.Column(db.Float, default=0.0)  # Store SOH Total Unit