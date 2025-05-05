from database import db  # Assuming db is imported in app.py

# class Packing(db.Model):
#     __tablename__ = 'packing'
#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     packing_date = db.Column(db.Date, nullable=False)
#     packing_code = db.Column(db.String(50), nullable=False)
#     description = db.Column(db.String(255))
#     units = db.Column(db.Float, default=0.0)
#     total_kg = db.Column(db.Float, default=0.0)
#     adjustment_kg = db.Column(db.Float, default=0.0)


class Packing(db.Model):
    __tablename__ = 'packing'

    id = db.Column(db.Integer, primary_key=True)
    packing_date = db.Column(db.Date, nullable=False)
    product_description = db.Column(db.String(255))
    product_code = db.Column(db.String(50), nullable=False)  # e.g., 2006.1 Frankfurter
    special_order_kg = db.Column(db.Float, default=0.0)  # B3: KG
    avg_weight_per_unit = db.Column(db.Float, nullable=False)  # F3: AVG Weight per Unit
    soh_requirement_units_week = db.Column(db.Integer, nullable=False)  # H3: SOH Requirement in Units/WEEK
    total_stock_multiplier = db.Column(db.Float)  # L3: User-entered multiplier (default 2)
    weekly_average = db.Column(db.Float)  # N3: User-entered variable
    requirements_kg = db.Column(db.Float, nullable=True)  # D3: Requirements in KG


    def __repr__(self):
        return f"<Packing {self.product_code} on {self.packing_date}>"