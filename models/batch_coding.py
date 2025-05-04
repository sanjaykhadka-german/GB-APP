from database import db  

class BatchCoding(db.Model):
    __tablename__ = 'batch_coding'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    batch_number = db.Column(db.String(50), nullable=False, unique=True)
    product = db.Column(db.String(50), nullable=False)
    
    
    