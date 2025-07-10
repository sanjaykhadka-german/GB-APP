# models/inventory.py
from sqlalchemy import Column, Integer, Float, ForeignKey, Date, String, func
from sqlalchemy.orm import relationship
from . import db

class Inventory(db.Model):
    __tablename__ = 'inventory'

    id = Column(Integer, primary_key=True)
    week_commencing = Column(Date, nullable=False)
    item_id = Column(Integer, ForeignKey('item_master.id'), nullable=False)
    required_total = Column(Float, default=0.0)  # From raw_material_report_table
    price_per_kg = Column(Float, default=0.0)    # From item_master
    value_required = Column(Float, default=0.0)   # required_total * price_per_kg
    current_stock = Column(Float, default=0.0)    # From raw_material_stocktake
    supplier_name = Column(String(255))           # From item_master
    required_for_plan = Column(Float, default=0.0)  # Sum of all daily required
    variance_for_week = Column(Float, default=0.0)  # current_stock - required_for_plan

    # Monday
    monday_opening_stock = Column(Float, default=0.0)  # current_stock for Monday, previous day's closing for others
    monday_required_kg = Column(Float, default=0.0)    # User input
    monday_variance = Column(Float, default=0.0)       # opening_stock - required_kg
    monday_to_be_ordered = Column(Float, default=0.0)  # User input
    monday_ordered_received = Column(Float, default=0.0)  # User input
    monday_consumed_kg = Column(Float, default=0.0)    # User input
    monday_closing_stock = Column(Float, default=0.0)  # opening_stock + ordered_received - consumed_kg

    # Tuesday
    tuesday_opening_stock = Column(Float, default=0.0)
    tuesday_required_kg = Column(Float, default=0.0)
    tuesday_variance = Column(Float, default=0.0)
    tuesday_to_be_ordered = Column(Float, default=0.0)
    tuesday_ordered_received = Column(Float, default=0.0)
    tuesday_consumed_kg = Column(Float, default=0.0)
    tuesday_closing_stock = Column(Float, default=0.0)

    # Wednesday
    wednesday_opening_stock = Column(Float, default=0.0)
    wednesday_required_kg = Column(Float, default=0.0)
    wednesday_variance = Column(Float, default=0.0)
    wednesday_to_be_ordered = Column(Float, default=0.0)
    wednesday_ordered_received = Column(Float, default=0.0)
    wednesday_consumed_kg = Column(Float, default=0.0)
    wednesday_closing_stock = Column(Float, default=0.0)

    # Thursday
    thursday_opening_stock = Column(Float, default=0.0)
    thursday_required_kg = Column(Float, default=0.0)
    thursday_variance = Column(Float, default=0.0)
    thursday_to_be_ordered = Column(Float, default=0.0)
    thursday_ordered_received = Column(Float, default=0.0)
    thursday_consumed_kg = Column(Float, default=0.0)
    thursday_closing_stock = Column(Float, default=0.0)

    # Friday
    friday_opening_stock = Column(Float, default=0.0)
    friday_required_kg = Column(Float, default=0.0)
    friday_variance = Column(Float, default=0.0)
    friday_to_be_ordered = Column(Float, default=0.0)
    friday_ordered_received = Column(Float, default=0.0)
    friday_consumed_kg = Column(Float, default=0.0)
    friday_closing_stock = Column(Float, default=0.0)

    # Saturday
    saturday_opening_stock = Column(Float, default=0.0)
    saturday_required_kg = Column(Float, default=0.0)
    saturday_variance = Column(Float, default=0.0)
    saturday_to_be_ordered = Column(Float, default=0.0)
    saturday_ordered_received = Column(Float, default=0.0)
    saturday_consumed_kg = Column(Float, default=0.0)
    saturday_closing_stock = Column(Float, default=0.0)

    # Sunday
    sunday_opening_stock = Column(Float, default=0.0)
    sunday_required_kg = Column(Float, default=0.0)
    sunday_variance = Column(Float, default=0.0)
    sunday_to_be_ordered = Column(Float, default=0.0)
    sunday_ordered_received = Column(Float, default=0.0)
    sunday_consumed_kg = Column(Float, default=0.0)
    sunday_closing_stock = Column(Float, default=0.0)

    # Relationships
    item = relationship('ItemMaster', backref='inventories')

    def calculate_daily_values(self):
        """Calculate all derived values for each day"""
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        # Calculate opening stocks and other values for each day
        for i, day in enumerate(days):
            # Get opening stock
            if i == 0:  # Monday
                opening_stock = self.current_stock
            else:  # Other days
                prev_day = days[i-1]
                opening_stock = getattr(self, f"{prev_day}_closing_stock")
            
            # Set opening stock
            setattr(self, f"{day}_opening_stock", opening_stock)
            
            # Calculate variance
            required = getattr(self, f"{day}_required_kg")
            variance = opening_stock - required
            setattr(self, f"{day}_variance", variance)
            
            # Calculate closing stock
            ordered_received = getattr(self, f"{day}_ordered_received")
            consumed = getattr(self, f"{day}_consumed_kg")
            closing_stock = opening_stock + ordered_received - consumed
            setattr(self, f"{day}_closing_stock", closing_stock)
        
        # Calculate totals
        self.required_for_plan = sum(getattr(self, f"{day}_required_kg") for day in days)
        self.variance_for_week = self.current_stock - self.required_for_plan
        self.value_required = self.required_for_plan * self.price_per_kg

    def update_field(self, field, value):
        """Update a field and recalculate all dependent values"""
        setattr(self, field, value)
        self.calculate_daily_values()
        return {
            'required_for_plan': self.required_for_plan,
            'variance_for_week': self.variance_for_week,
            'value_required': self.value_required,
            'opening_stock': getattr(self, f"{field.split('_')[0]}_opening_stock"),
            'variance': getattr(self, f"{field.split('_')[0]}_variance"),
            'closing_stock': getattr(self, f"{field.split('_')[0]}_closing_stock")
        }