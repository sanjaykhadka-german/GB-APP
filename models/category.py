from database import db

class Category(db.Model):
    __tablename__ = 'category'
    categoryID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    categoryName = db.Column(db.String(50), nullable=False, unique=True)