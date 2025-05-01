from database import db

class TraceabilityProduction(db.Model):
    __tablename__ = 'traceability_production'
    id = db.Column(db.Integer, primary_key=True)
    production_plan_id = db.Column(db.Integer, db.ForeignKey('production_plan.id'), nullable=False)
    product_description = db.Column(db.Text, nullable=False)
    batch_number = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    weight = db.Column(db.Numeric(precision=10, scale=2), nullable=False)

    # Relationship
    #production_plan = db.relationship('ProductionPlan', backref=db.backref('traceability_productions', lazy=True))