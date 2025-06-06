from database import db
from sqlalchemy import Column, Integer, String, Numeric, Date

class RecipeMaster(db.Model):
    __tablename__ = 'recipe_master'

    id = Column(Integer, primary_key=True)
    recipe_code = Column(String(50), nullable=False)
    description = Column(String(200), nullable=False)
    raw_material = Column(String(200), nullable=False)
    kg_per_batch = Column(Numeric(10, 3), nullable=False)
    percentage = Column(Numeric(5, 2), nullable=False, default=0)
    week_commencing = Column(Date, nullable=False)

    def __repr__(self):
        return f'<RecipeMaster {self.recipe_code}>'