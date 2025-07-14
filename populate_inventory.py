from app import app, db
from models import ItemMaster, ItemType, RawMaterialStocktake, RawMaterialReportTable, Production, RecipeMaster, Inventory
from sqlalchemy import func
from datetime import timedelta

def get_daily_required_kg(db_session, week_commencing, raw_material_item_id):
    """
    Calculate the required kg for a specific raw material for each day of the week.
    Uses the planned values (monday_planned, tuesday_planned, etc.) from Production records.
    """
    daily_reqs = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]  # [Mon, Tue, Wed, Thu, Fri, Sat, Sun]

    # Find all production records for the given week
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

        # Calculate raw material requirements for each day using planned values
        for recipe in recipes:
            component_qty = float(recipe.quantity_kg or 0)
            
            # Calculate the proportion of this raw material in the recipe
            component_proportion = component_qty / float(total_recipe_qty) if total_recipe_qty > 0 else 0
            
            # Monday required kg
            monday_planned = float(prod.monday_planned or 0)
            daily_reqs[0] += monday_planned * component_proportion
            
            # Tuesday required kg
            tuesday_planned = float(prod.tuesday_planned or 0)
            daily_reqs[1] += tuesday_planned * component_proportion
            
            # Wednesday required kg
            wednesday_planned = float(prod.wednesday_planned or 0)
            daily_reqs[2] += wednesday_planned * component_proportion
            
            # Thursday required kg
            thursday_planned = float(prod.thursday_planned or 0)
            daily_reqs[3] += thursday_planned * component_proportion
            
            # Friday required kg
            friday_planned = float(prod.friday_planned or 0)
            daily_reqs[4] += friday_planned * component_proportion
            
            # Saturday required kg
            saturday_planned = float(prod.saturday_planned or 0)
            daily_reqs[5] += saturday_planned * component_proportion
            
            # Sunday required kg
            sunday_planned = float(prod.sunday_planned or 0)
            daily_reqs[6] += sunday_planned * component_proportion
            
    return daily_reqs  # Return as a list [Mon, Tue, Wed, Thu, Fri, Sat, Sun]

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
            
            # Get all raw materials from raw_material_report_table instead of filtering by item type
            # This ensures we include all items that are actually used as raw materials
            raw_material_items = db.session.query(
                RawMaterialReportTable.raw_material_id
            ).filter(
                RawMaterialReportTable.week_commencing == week
            ).distinct().all()
            
            # Get the actual ItemMaster objects
            raw_materials = []
            for item_id in raw_material_items:
                item = ItemMaster.query.get(item_id[0])
                if item:
                    raw_materials.append(item)
            
            print(f"Found {len(raw_materials)} raw materials from reports")

            for rm in raw_materials:
                # Check if inventory record already exists
                inv = db.session.query(Inventory).filter_by(week_commencing=week, item_id=rm.id).first()
                if not inv:
                    inv = Inventory(week_commencing=week, item_id=rm.id)
                    db.session.add(inv)
                
                # Rest of the logic remains the same...
                # G: SOH - from raw_material_stocktake
                stocktake = db.session.query(RawMaterialStocktake).filter(
                    RawMaterialStocktake.item_code == rm.item_code,
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