from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import db

class RecipeMaster(db.Model):
    __tablename__ = 'recipe_master'

    id = Column(Integer, primary_key=True)
    recipe_code = Column(String(100), nullable=False)
    description = Column(String(255))
    kg_per_batch = Column(Float)
    percentage = Column(Float)
    raw_material_id = Column(Integer, ForeignKey('raw_materials.id'))
    
    # Relationship
    raw_material = relationship('RawMaterials', backref='recipes')

    def __repr__(self):
        return f'<RecipeMaster {self.recipe_code}>'