from database import db

class ItemMaster(db.Model):
    __tablename__ = 'item_master'
    itemID = db.Column(db.String(255), primary_key=True)
    itemName = db.Column(db.String(255), nullable=False)
    itemDescription = db.Column(db.String(255))
    itemTypeID = db.Column(db.String(255), db.ForeignKey('item_type.itemTypeID'))
    categoryID = db.Column(db.String(255), db.ForeignKey('category.categoryID'))
    departmentID = db.Column(db.String(255), db.ForeignKey('department.departmentID'))
    machineID = db.Column(db.String(255), db.ForeignKey('machinery.machineID'))
    kg_per_box = db.Column(db.Numeric(20, 3))
    kg_per_each = db.Column(db.Numeric(20, 3))
    units_per_box = db.Column(db.Integer)
    stock_item = db.Column(db.Boolean, default=True)
    min_stocks_in_boxes = db.Column(db.Integer)
    max_stocks_in_boxes = db.Column(db.Integer)
    fill_weight = db.Column(db.Numeric(20, 3))
    casing = db.Column(db.String(255))
    ideal_batch_size = db.Column(db.Integer)

    category = db.relationship('Category', backref='item_masters')
    department = db.relationship('Department', backref='item_masters')
    machine = db.relationship('Machinery', backref='item_masters')
    item_type = db.relationship('ItemType', backref='item_masters')