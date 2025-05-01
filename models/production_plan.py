from database import db
from datetime import date

class ProductionPlan(db.Model):
    __tablename__ = 'production_plan'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    description_id = db.Column(db.Integer, db.ForeignKey('finished_goods.id'), nullable=False)
    batches = db.Column(db.Float, default=0.0)
    weight = db.Column(db.Float, default=0.0)
    actual = db.Column(db.Float, default=0.0)
    batch_number_id = db.Column(db.Integer, db.ForeignKey('machinery.machineID'), nullable=False)
    production_date = db.Column(db.Date, nullable=False)
    machineID = db.Column(db.Integer, db.ForeignKey('machinery.machineID'), nullable=False)
    priority = db.Column(db.Float, default=0.0)
    status = db.Column(db.Enum('Planned', 'In Progress', 'Completed'), default='Planned')
    comments = db.Column(db.Text)
    operator_id = db.Column(db.Integer, db.ForeignKey('operator.id'))
    signature = db.Column(db.String(255))
    room = db.Column(db.Enum('Room A', 'Room B', 'Room C'), default='Room A')
    traceability_production_id = db.Column(db.Integer, db.ForeignKey('traceability_production.id'))
    raw_weight = db.Column(db.Float, default=0.0)
    actual_injected_weight = db.Column(db.Float, default=0.0)
    cooking_record_id = db.Column(db.Integer, db.ForeignKey('cooking_record.id'))

    # Relationships
    description = db.relationship('FinishedGoods', backref='production_plans', foreign_keys=[description_id])
    batch_number = db.relationship('Machinery', backref='batch_numbers', foreign_keys=[batch_number_id])
    machine = db.relationship('Machinery', backref='production_plans', foreign_keys=[machineID])
    operator = db.relationship('Operator', backref='production_plans', foreign_keys=[operator_id])
    traceability_production = db.relationship('TraceabilityProduction', backref='production_plans', foreign_keys=[traceability_production_id])
    cooking_record = db.relationship('CookingRecord', backref='production_plans', foreign_keys=[cooking_record_id])

    # Calculated properties
    @property
    def injected_weight(self):
        from models.injected_products import InjectedProducts
        injected_product = InjectedProducts.query.filter_by(product_id=self.description_id).first()
        injection_rate = injected_product.injection_rate if injected_product else 0.0
        return (self.raw_weight * (100 + injection_rate)) / 100 if self.raw_weight else 0.0

    @property
    def actual_percentage_injected(self):
        if self.raw_weight and self.actual_injected_weight:
            return ((self.actual_injected_weight / self.raw_weight) * 100) - 100
        return 0.0