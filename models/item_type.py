from database import db

class ItemType(db.Model):
    __tablename__ = 'item_type'
    itemTypeID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    itemTypeName = db.Column(db.String(50), nullable=False)