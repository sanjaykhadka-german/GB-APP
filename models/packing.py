# models/packing.py
from sqlalchemy import UniqueConstraint
from database import db
from datetime import date

class Packing(db.Model):
    __tablename__ = 'packing'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    week_commencing = db.Column(db.Date, nullable=True)
    packing_date = db.Column(db.Date, nullable=False)
    product_code = db.Column(db.String(50), nullable=False)
    product_description = db.Column(db.String(255))
    special_order_kg = db.Column(db.Float, default=0.0)
    special_order_unit = db.Column(db.Integer, default=0)
    requirement_kg = db.Column(db.Float, default=0.0)
    requirement_unit = db.Column(db.Integer, default=0)
    avg_weight_per_unit = db.Column(db.Float, default=0.0)
    soh_requirement_kg_week = db.Column(db.Float, default=0.0)
    soh_requirement_units_week = db.Column(db.Integer, default=0)
    soh_kg = db.Column(db.Float, default=0.0)
    soh_units = db.Column(db.Float, default=0.0)
    avg_weight_per_unit_calc = db.Column(db.Float, default=0.0)
    total_stock_kg = db.Column(db.Float, default=0.0)
    total_stock_units = db.Column(db.Integer, default=0)
    weekly_average = db.Column(db.Float, default=0.0)
    priority = db.Column(db.Integer, default=0)

    __table_args__ = (
        db.ForeignKeyConstraint(
            ['week_commencing', 'product_code'],
            ['soh.week_commencing', 'soh.fg_code'],
            name='fk_packing_soh_week_commencing_product_code'
        ),
        UniqueConstraint('week_commencing', 'product_code', name='uq_packing_week_product')
    )

    def __repr__(self):
        return f"<Packing {self.product_code} - {self.packing_date}>"