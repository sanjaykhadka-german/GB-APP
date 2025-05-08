# from database import db  


# class Packing(db.Model):
#     __tablename__ = 'packing'

#     id = db.Column(db.Integer, primary_key=True)
#     packing_date = db.Column(db.Date, nullable=False)
#     product_description = db.Column(db.String(255))
#     product_code = db.Column(db.String(50), nullable=False)  # e.g., 2006.1 Frankfurter
#     special_order_kg = db.Column(db.Float, default=0.0)  # B3: KG
#     avg_weight_per_unit = db.Column(db.Float, nullable=False)  # F3: AVG Weight per Unit
#     soh_requirement_units_week = db.Column(db.Integer, nullable=False)  # H3: SOH Requirement in Units/WEEK
#     total_stock_multiplier = db.Column(db.Float)  # L3: User-entered multiplier (default 2)
#     weekly_average = db.Column(db.Float)  # N3: User-entered variable
#     requirements_kg = db.Column(db.Float, nullable=True)  # D3: Requirements in KG


#     def __repr__(self):
#         return f"<Packing {self.product_code} on {self.packing_date}>"


from database import db
from datetime import date

class Packing(db.Model):
    __tablename__ = 'packing'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    packing_date = db.Column(db.Date, nullable=False)  # A2: Date
    product_code = db.Column(db.String(50), nullable=False)  # B2: Product Code
    product_description = db.Column(db.String(255))  # C2: Product Description
    special_order_kg = db.Column(db.Float, default=0.0)  # D2: Special Orders KG
    special_order_unit = db.Column(db.Integer, default=0)  # E2: Special Orders Unit (calculated)
    requirement_kg = db.Column(db.Float, default=0.0)  # F2: Requirement This KG (calculated)
    requirement_unit = db.Column(db.Integer, default=0)  # G2: Requirements This Unit (calculated)
    avg_weight_per_unit = db.Column(db.Float, default=0.0)  # H2: AVG Weight per Unit
    soh_requirement_kg_week = db.Column(db.Float, default=0.0)  # I2: SOH Requirement in KG/WEEK (calculated)
    soh_requirement_units_week = db.Column(db.Integer, default=0)  # J2: SOH Requirement in Units/WEEK
    soh_kg = db.Column(db.Float, default=0.0)  # K2: SOH KG (calculated)
    soh_units = db.Column(db.Float, default=0.0)  # L2: SOH UNITS (from SOH table)
    avg_weight_per_unit_calc = db.Column(db.Float, default=0.0)  # M2: Avg Weight in KG per Unit (same as H2)
    total_stock_kg = db.Column(db.Float, default=0.0)  # N2: Total Stock KG (calculated)
    total_stock_units = db.Column(db.Integer, default=0)  # O2: Total Stock UNITS (calculated)
    weekly_average = db.Column(db.Float, default=0.0)  # P2: Weekly Average

    def __repr__(self):
        return f"<Packing {self.product_code} - {self.packing_date}>"