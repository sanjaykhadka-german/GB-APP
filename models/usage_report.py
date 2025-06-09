from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import db

class UsageReport(db.Model):
    __tablename__ = 'usage_report'

    id = Column(Integer, primary_key=True)
    week_commencing = Column(Date)
    production_date = Column(Date, nullable=False)
    recipe_code = Column(String(50), nullable=False)
    raw_material = Column(String(255), nullable=False)
    usage_kg = Column(Float, nullable=False)
    percentage = Column(Float, nullable=False)
    created_at = Column(DateTime)
    raw_material_id = Column(Integer, ForeignKey('raw_materials.id'))

    # Relationship
    raw_material_ref = relationship('RawMaterials', backref='usage_reports')

    def __repr__(self):
        return f'<UsageReport {self.raw_material} - {self.production_date}>' 