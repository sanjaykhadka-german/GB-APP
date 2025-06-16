from sqlalchemy import UniqueConstraint, ForeignKeyConstraint
from database import db
from datetime import date

class Packing(db.Model):
    __tablename__ = 'packing'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    week_commencing = db.Column(db.Date, nullable=True)  # Matches DEFAULT NULL
    packing_date = db.Column(db.Date, nullable=False)
    product_code = db.Column(db.String(50), nullable=False)
    product_description = db.Column(db.String(255), nullable=True)
    special_order_kg = db.Column(db.Float, default=0.0, nullable=True)
    special_order_unit = db.Column(db.Integer, default=0, nullable=True)
    requirement_kg = db.Column(db.Float, default=0.0, nullable=True)
    requirement_unit = db.Column(db.Integer, default=0, nullable=True)
    avg_weight_per_unit = db.Column(db.Float, default=0.0, nullable=True)
    soh_requirement_kg_week = db.Column(db.Float, default=0.0, nullable=True)
    soh_requirement_units_week = db.Column(db.Integer, default=0, nullable=True)
    soh_kg = db.Column(db.Float, default=0.0, nullable=True)
    soh_units = db.Column(db.Float, default=0.0, nullable=True)
    total_stock_kg = db.Column(db.Float, default=0.0, nullable=True)
    total_stock_units = db.Column(db.Integer, default=0, nullable=True)
    weekly_average = db.Column(db.Float, default=0.0, nullable=True)
    priority = db.Column(db.Integer, default=0, nullable=True)
    machinery = db.Column(db.Integer, nullable=True)  # Matches DEFAULT NULL

    __table_args__ = (
        ForeignKeyConstraint(
            ['week_commencing', 'product_code'],
            ['soh.week_commencing', 'soh.fg_code'],
            name='fk_packing_soh_week_commencing_product_code'
        ),
        ForeignKeyConstraint(
            ['machinery'],
            ['machinery.machineID'],
            name='packing_ibfk_1'
        ),
        UniqueConstraint(
            'week_commencing', 'product_code', 'packing_date', 'machinery',
            name='uq_packing_week_product_date_machinery'
        ),
    )

    def __repr__(self):
        return f"<Packing {self.product_code} - {self.packing_date}>"