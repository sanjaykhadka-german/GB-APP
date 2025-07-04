#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models.packing import Packing
from models.production import Production
from models.item_master import ItemMaster
from models.item_type import ItemType
from sqlalchemy import func
from datetime import datetime
from controllers.packing_controller import re_aggregate_filling_and_production_for_date

def fix_production_totals():
    try:
        # Get all production entries
        productions = Production.query.all()
        
        for prod in productions:
            # Get the packing entries for this production's date and week
            packings = Packing.query.filter(
                Packing.packing_date == prod.production_date,
                Packing.week_commencing == prod.week_commencing
            ).all()
            
            # Group packings by recipe family
            recipe_family_totals = {}
            for packing in packings:
                if not packing.item:
                    continue
                    
                recipe_family = packing.item.item_code.split('.')[0]
                if recipe_family not in recipe_family_totals:
                    recipe_family_totals[recipe_family] = 0.0
                recipe_family_totals[recipe_family] += packing.requirement_kg or 0.0
            
            # Update production code and totals if needed
            for recipe_family, total_kg in recipe_family_totals.items():
                # Find WIP item for this recipe family
                wip_item = ItemMaster.query.join(ItemMaster.item_type).filter(
                    ItemMaster.item_code == recipe_family,
                    ItemMaster.item_type.has(type_name='WIP')
                ).first()
                
                if not wip_item:
                    print(f"No WIP item found for recipe family {recipe_family}")
                    continue
                
                # Update production entry
                if prod.production_code != recipe_family:
                    print(f"Updating production code from {prod.production_code} to {recipe_family}")
                    prod.production_code = recipe_family
                    prod.item_id = wip_item.id
                    prod.description = wip_item.description
                
                # Update totals
                if total_kg > 0:
                    batches = total_kg / 300.0  # Using 300kg batch size
                    prod.batches = batches
                    prod.total_kg = total_kg
                    print(f"Updated totals for {recipe_family}: {total_kg}kg, {batches} batches")
        
        db.session.commit()
        print("Production totals updated successfully")
        
        # Re-aggregate all dates to ensure consistency
        dates_to_reaggregate = set((p.production_date, p.week_commencing) for p in productions)
        for prod_date, week_comm in dates_to_reaggregate:
            print(f"Re-aggregating for date {prod_date}, week {week_comm}")
            re_aggregate_filling_and_production_for_date(prod_date, week_comm)
        
        print("Re-aggregation complete")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error fixing production totals: {str(e)}")
        raise e

if __name__ == "__main__":
    with app.app_context():
        fix_production_totals() 