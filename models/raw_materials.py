from sqlalchemy import Column, Integer, String
from database import db

class RawMaterials(db.Model):
    __tablename__ = 'raw_materials'

    id = Column(Integer, primary_key=True)
    raw_material = Column(String(255), nullable=False, unique=True)

    def __repr__(self):
        return f'<RawMaterials {self.raw_material}>' 