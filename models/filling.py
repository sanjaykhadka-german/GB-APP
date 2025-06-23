from database import db  

class Filling(db.Model):
    __tablename__ = 'filling'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    week_commencing = db.Column(db.Date, nullable=True)  # New column
    filling_date = db.Column(db.Date, nullable=False)
    
    # Foreign key to ItemMaster instead of fill_code string (references WIPF items)
    item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)
    
    # Keep fill_code temporarily for migration compatibility (will be removed later)
    fill_code = db.Column(db.String(50), nullable=True)
    description = db.Column(db.String(255))
    kilo_per_size = db.Column(db.Float, default=0.0)

    # Relationships
    item = db.relationship('ItemMaster', backref='filling_records')

    def __repr__(self):
        return f"<Filling {self.item.item_code if self.item else self.fill_code} - {self.filling_date}>"