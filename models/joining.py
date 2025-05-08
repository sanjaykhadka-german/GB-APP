from database import db

# class Joining(db.Model):
#     __tablename__ = 'joining'
#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     fg_code = db.Column(db.String(50), nullable=False)
#     description = db.Column(db.String(255))
#     fw = db.Column(db.Boolean, default=False)
#     make_to_order = db.Column(db.Boolean, default=False)
#     min_level = db.Column(db.Float)
#     max_level = db.Column(db.Float)
#     kg_per_unit = db.Column(db.Float)
#     loss = db.Column(db.Float)
#     filling_code = db.Column(db.String(50))
#     filling_description = db.Column(db.String(255))
#     production = db.Column(db.String(50))



class Joining(db.Model):
    __tablename__ = 'joining'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fg_code = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    fw = db.Column(db.Boolean, default=False)
    make_to_order = db.Column(db.Boolean, default=False)
    min_level = db.Column(db.Float)
    max_level = db.Column(db.Float)
    kg_per_unit = db.Column(db.Float)
    loss = db.Column(db.Float)
    filling_code = db.Column(db.String(50))
    filling_description = db.Column(db.String(255))
    production = db.Column(db.String(50))
    units_per_bag = db.Column(db.Float)  # <-- New column




    