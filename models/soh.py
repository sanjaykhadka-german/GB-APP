# models/soh.py
from database import db

class SOH(db.Model):
    __tablename__ = 'soh'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    week_commencing = db.Column(db.Date, nullable=True)
    fg_code = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    soh_dispatch_boxes = db.Column(db.Float, default=0.0)
    soh_dispatch_units = db.Column(db.Float, default=0.0)
    soh_packing_boxes = db.Column(db.Float, default=0.0)
    soh_packing_units = db.Column(db.Float, default=0.0)
    soh_total_boxes = db.Column(db.Float, default=0.0)
    soh_total_units = db.Column(db.Float, default=0.0)
    edit_date = db.Column(db.DateTime, default=db.func.current_timestamp())

    __table_args__ = (
        db.UniqueConstraint('week_commencing', 'fg_code', name='uix_soh_week_commencing_fg_code'),
    )