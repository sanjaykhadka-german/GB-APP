from app import app
from database import db
from models.raw_material_report_table import RawMaterialReportTable
from models.usage_report_table import UsageReportTable
from models.item_master import ItemMaster
from models.production import Production
from models.recipe_master import RecipeMaster
from models.item_type import ItemType
from datetime import datetime, timedelta
from sqlalchemy import func

def get_week_dates(date):
    """Get all dates for the week starting from the given date"""
    week_dates = []
    for i in range(5):  # Monday to Friday
        week_dates.append(date + timedelta(days=i))
    return week_dates

def populate_report_tables():
    with app.app_context():
        try:
            # Clear existing data
            db.session.query(RawMaterialReportTable).delete()
            db.session.query(UsageReportTable).delete()
            db.session.commit()
            
            # Get RM type ID
            rm_type = ItemType.query.filter_by(type_name='RM').first()
            if not rm_type:
                print("Error: RM item type not found")
                return
            
            # Get all raw materials
            raw_materials = ItemMaster.query.filter_by(item_type_id=rm_type.id).all()
            print(f"\nFound {len(raw_materials)} raw materials")
            
            # Get all production weeks
            production_weeks = db.session.query(func.date(Production.production_date)).distinct().all()
            weeks = [week[0] for week in production_weeks]
            print(f"Found {len(weeks)} production weeks")
            
            # Process each week
            for week_commencing in weeks:
                print(f"\nProcessing week: {week_commencing}")
                week_dates = get_week_dates(week_commencing)
                print(f"Week dates: {', '.join(str(d) for d in week_dates)}")
                
                # Process each raw material
                for raw_material in raw_materials:
                    print(f"\nProcessing raw material: {raw_material.item_code} - {raw_material.description}")
                    
                    # Get all recipes using this raw material
                    recipes = RecipeMaster.query.filter_by(component_item_id=raw_material.id).all()
                    print(f"Found {len(recipes)} recipes using this raw material")
                    
                    if not recipes:
                        continue
                    
                    # Calculate daily usage
                    daily_usage = {date: 0.0 for date in week_dates}
                    total_usage = 0.0
                    
                    for recipe in recipes:
                        print(f"Processing recipe for product: {recipe.recipe_wip.description if recipe.recipe_wip else 'N/A'}")
                        # Get production records for this recipe's product
                        productions = Production.query.filter(
                            Production.item_id == recipe.recipe_wip_id,
                            Production.production_date.in_(week_dates)
                        ).all()
                        print(f"Found {len(productions)} production records")
                        
                        for prod in productions:
                            usage = float(prod.total_kg or 0) * float(recipe.quantity_kg or 0)
                            daily_usage[prod.production_date] += usage
                            total_usage += usage
                            print(f"Production date: {prod.production_date}, Total KG: {prod.total_kg}, Recipe qty: {recipe.quantity_kg}, Usage: {usage}")
                    
                    if total_usage > 0:
                        print(f"Total usage for {raw_material.item_code}: {total_usage}")
                        print(f"Daily usage: {daily_usage}")
                        
                        # Create usage report
                        usage_report = UsageReportTable(
                            week_commencing=week_commencing,
                            item_id=raw_material.id,
                            monday=daily_usage.get(week_dates[0], 0),
                            tuesday=daily_usage.get(week_dates[1], 0),
                            wednesday=daily_usage.get(week_dates[2], 0),
                            thursday=daily_usage.get(week_dates[3], 0),
                            friday=daily_usage.get(week_dates[4], 0),
                            total_usage=total_usage
                        )
                        db.session.add(usage_report)
                        
                        # Create raw material report
                        raw_material_report = RawMaterialReportTable(
                            week_commencing=week_commencing,
                            item_id=raw_material.id,
                            required_total_production=total_usage,
                            value_required_rm=total_usage * float(raw_material.price_per_kg or 0),
                            current_stock=0.00,  # Will be updated from stocktake
                            required_for_plan=total_usage,
                            variance_week=0.00,  # Will be calculated after stocktake
                            kg_required=daily_usage.get(week_dates[0], 0),  # Monday's requirement
                            variance=0.00  # Will be calculated after stocktake
                        )
                        db.session.add(raw_material_report)
                
                db.session.commit()
                print(f"Completed week: {week_commencing}")
            
            print("\nFinal counts:")
            print(f"Raw Material Reports: {RawMaterialReportTable.query.count()}")
            print(f"Usage Reports: {UsageReportTable.query.count()}")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    populate_report_tables() 