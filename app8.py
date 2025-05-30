from models import SOH, Joining, Packing
from datetime import datetime

week_commencing = datetime(2025, 6, 2).date()
soh_6002 = SOH.query.filter(SOH.fg_code.ilike('6002%'), SOH.week_commencing == week_commencing).all()
joining_6002 = Joining.query.filter(Joining.fg_code.ilike('6002%')).all()
packings_6002 = Packing.query.filter(Packing.product_code.ilike('6002%'), Packing.week_commencing == week_commencing).all()

print("SOH:", [(s.fg_code, s.soh_total_units, s.min_level, s.max_level) for s in soh_6002])
print("Joining:", [(j.fg_code, j.kg_per_unit, j.min_level, j.max_level) for j in joining_6002])
print("Packings:", [(p.product_code, p.requirement_kg, p.soh_requirement_units_week, p.weekly_average, p.avg_weight_per_unit) for p in packings_6002])