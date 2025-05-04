from database import db


class FilmWaste(db.Model):
    __tablename__ = 'film_waste'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    
    
    