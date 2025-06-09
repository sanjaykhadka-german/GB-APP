from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import db
from datetime import date

class UsageReport(db.Model):
    __tablename__ = 'usage'

    id = Column(Integer, primary_key=True)
    week_commencing = Column(Date, nullable=False)
    production_date = Column(Date, nullable=False)
    raw_material_id = Column(Integer, ForeignKey('raw_materials.id'), nullable=False)
    usage_kg = Column(Float, nullable=False)
    
    # Relationship
    raw_material = relationship('RawMaterials', backref='usage_reports')

    def __repr__(self):
        return f'<UsageReport {self.raw_material} - {self.production_date}>'