from app import app, db
from models import ItemMaster, ItemType, RawMaterialStocktake, RawMaterialReportTable, Production, RecipeMaster, Inventory
from sqlalchemy import func
from datetime import timedelta

def get_daily_required_kg(db_session, week_commencing, raw_material_item_id):
    """
    Calculate the required kg for a specific raw material for each day of the week.
    """
    daily_reqs = {i: 0.0 for i in range(7)}  # Monday is 0, Sunday is 6

    # Find all production planned for the given week
    productions_in_week = db_session.query(Production).filter(
        Production.week_commencing == week_commencing
    ).all()

    for prod in productions_in_week:
        # Find all recipes for the produced item that use the specified raw material
        recipes = db_session.query(RecipeMaster).filter(
            RecipeMaster.recipe_wip_id == prod.item_id,
            RecipeMaster.component_item_id == raw_material_item_id
        ).all()
        
        if not recipes:
            continue

        # Get the total recipe quantity for the produced item to calculate proportions
        total_recipe_qty = db_session.query(func.sum(RecipeMaster.quantity_kg)).filter(
            RecipeMaster.recipe_wip_id == prod.item_id
        ).scalar() or 0
        
        if total_recipe_qty == 0:
            continue

        day_of_week = prod.production_date.weekday()
        
        for recipe in recipes:
            component_qty = float(recipe.quantity_kg or 0)
            prod_qty = float(prod.total_kg or 0)
            
            # Apportion the production quantity based on the recipe's component weight
            usage_for_production = (component_qty / float(total_recipe_qty)) * prod_qty
            daily_reqs[day_of_week] += usage_for_production
            
    return [daily_reqs[i] for i in range(7)] # Return as a list [Mon, Tue, ...]

def populate_inventory(weeks_to_process):
    """
    Populates the inventory table for all raw materials for a given set of weeks.
    """
    with app.app_context():
        if not weeks_to_process:
            print("populate_inventory: No weeks to process.")
            return

        for week in weeks_to_process:
            print(f"Populating inventory for week: {week}")
            # Get all raw materials
            raw_materials = db.session.query(ItemMaster).join(ItemType).filter(ItemType.type_name == 'RM').all()

            for rm in raw_materials:
                # Check if inventory record already exists
                inv = db.session.query(Inventory).filter_by(week_commencing=week, item_id=rm.id).first()
                if not inv:
                    inv = Inventory(week_commencing=week, item_id=rm.id)
                    db.session.add(inv)
                
                # A & B: Week and Item are set by the loop/query
                
                # G: SOH - from raw_material_stocktake
                stocktake = db.session.query(RawMaterialStocktake).filter(
                    RawMaterialStocktake.item_code == rm.item_code,
                    # Assuming we use the stocktake from the same week
                    RawMaterialStocktake.week_commencing == week
                ).first()
                inv.soh = float(stocktake.current_stock) if stocktake and stocktake.current_stock else 0.0

                # L, S, Z, AG, AN, AU, BB: Daily required KG
                daily_reqs = get_daily_required_kg(db.session, week, rm.id)
                inv.monday_required_kg, inv.tuesday_required_kg, inv.wednesday_required_kg, \
                inv.thursday_required_kg, inv.friday_required_kg, inv.saturday_required_kg, \
                inv.sunday_required_kg = daily_reqs

                # C: Required in TOTAL for production
                inv.required_in_total = sum(daily_reqs)

                # D, E, H: Category, Price, Supplier from Item Master
                inv.price_per_kg = float(rm.price_per_kg or 0.0)
                inv.supplier_name = rm.supplier_name
                # Category requires a join, handled in controller for display

                # F: $ Value for Required RM
                inv.value_required_rm = inv.required_in_total * inv.price_per_kg

                # I: Required for plan (sum of daily requirements)
                inv.required_for_plan = inv.required_in_total

                # J: Variance for the week
                inv.variance_week = inv.soh - inv.required_for_plan

                # K: Monday opening stock is SOH
                inv.monday_opening_stock = inv.soh
                
                # M: Monday variance
                inv.monday_variance = inv.monday_opening_stock - inv.monday_required_kg
                
                # Q: Monday closing stock (based on user inputs being 0 initially)
                inv.monday_closing_stock = inv.monday_opening_stock + inv.monday_ordered_received - inv.monday_consumed_kg
                
                # Subsequent days
                inv.tuesday_opening_stock = inv.monday_closing_stock
                inv.tuesday_variance = inv.tuesday_opening_stock - inv.tuesday_required_kg
                inv.tuesday_closing_stock = inv.tuesday_opening_stock + inv.tuesday_ordered_received - inv.tuesday_consumed_kg
                
                inv.wednesday_opening_stock = inv.tuesday_closing_stock
                inv.wednesday_variance = inv.wednesday_opening_stock - inv.wednesday_required_kg
                inv.wednesday_closing_stock = inv.wednesday_opening_stock + inv.wednesday_ordered_received - inv.wednesday_consumed_kg

                inv.thursday_opening_stock = inv.wednesday_closing_stock
                inv.thursday_variance = inv.thursday_opening_stock - inv.thursday_required_kg
                inv.thursday_closing_stock = inv.thursday_opening_stock + inv.thursday_ordered_received - inv.thursday_consumed_kg

                inv.friday_opening_stock = inv.thursday_closing_stock
                inv.friday_variance = inv.friday_opening_stock - inv.friday_required_kg
                inv.friday_closing_stock = inv.friday_opening_stock + inv.friday_ordered_received - inv.friday_consumed_kg

                inv.saturday_opening_stock = inv.friday_closing_stock
                inv.saturday_variance = inv.saturday_opening_stock - inv.saturday_required_kg
                inv.saturday_closing_stock = inv.saturday_opening_stock + inv.saturday_ordered_received - inv.saturday_consumed_kg

                inv.sunday_opening_stock = inv.saturday_closing_stock
                inv.sunday_variance = inv.sunday_opening_stock - inv.sunday_required_kg
                inv.sunday_closing_stock = inv.sunday_opening_stock + inv.sunday_ordered_received - inv.sunday_consumed_kg

            db.session.commit()
            print(f"Finished populating inventory for week: {week}") 