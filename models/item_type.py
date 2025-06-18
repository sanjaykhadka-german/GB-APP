from database import db

class ItemType(db.Model):
    __tablename__ = 'item_type'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type_name = db.Column(db.String(50), nullable=False, unique=True)                

    def __repr__(self):
        return f'<ItemType {self.type_name}>'