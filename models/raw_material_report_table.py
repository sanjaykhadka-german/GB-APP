from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import db
from datetime import datetime

class RawMaterialReportTable(db.Model):
    __tablename__ = 'raw_material_report_table'

    id = Column(Integer, primary_key=True)
    week_commencing = Column(Date)
    production_date = Column(Date, nullable=False)
    raw_material_id = Column(Integer)  # Matches database structure
    raw_material = Column(String(255), nullable=False)
    meat_required = Column(Float, nullable=False)  # Matches database structure
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Add property to maintain backward compatibility
    @property
    def usage_kg(self):
        return self.meat_required
    
    @usage_kg.setter
    def usage_kg(self, value):
        self.meat_required = value

    def __repr__(self):
        return f'<RawMaterialReportTable {self.raw_material} - {self.production_date}>' 
    
