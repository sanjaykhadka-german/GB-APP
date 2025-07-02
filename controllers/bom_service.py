"""
BOM (Bill of Materials) Explosion Service
Handles automatic creation of downstream production requirements
Uses existing RecipeMaster model with current field names
"""
from app import db
from models.packing import Packing
from models.filling import Filling  
from models.production import Production
from models.item_master import ItemMaster
from models.recipe_master import RecipeMaster
from models.item_type import ItemType
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

def update_downstream_requirements(packing_date, week_commencing):
    """
    Aggregates all packing requirements for a given day and updates/creates
    the corresponding Filling and Production plans. This is the "Recipe Explosion".
    
    Args:
        packing_date: Date for which to calculate requirements
        week_commencing: Week commencing date for planning period
    """
    try:
        logger.info(f"Starting recipe explosion for {packing_date}, week {week_commencing}")
        
        # Step 1: Aggregate all packing requirements for the day by item
        daily_packing_reqs = db.session.query(
            Packing.item_id,
            func.sum(Packing.requirement_kg).label('total_req_kg')
        ).filter(
            Packing.packing_date == packing_date,
            Packing.week_commencing == week_commencing,
            Packing.requirement_kg > 0
        ).group_by(Packing.item_id).all()

        if not daily_packing_reqs:
            logger.info("No packing requirements found for the specified date")
            return True, "No packing requirements to process"

        # Dictionaries to hold aggregated needs
        filling_needs = {}  # {wipf_item_id: total_kg}
        production_needs = {}  # {wip_item_id: total_kg}

        # Step 2: Explode the recipes for each packed item
        for packed_item_id, total_req_kg in daily_packing_reqs:
            logger.info(f"Processing recipes for item_id {packed_item_id}: {total_req_kg} kg required")
            
            # Get all recipe components for this finished good
            recipe_components = RecipeMaster.query.filter_by(
                finished_good_id=packed_item_id
            ).join(ItemMaster, RecipeMaster.raw_material_id == ItemMaster.id).all()
            
            for recipe in recipe_components:
                component_item = recipe.raw_material_item
                if not component_item:
                    continue
                
                # Calculate component requirement based on recipe
                # Using kg_per_batch if available, otherwise percentage
                if recipe.kg_per_batch and recipe.kg_per_batch > 0:
                    needed_kg = total_req_kg * recipe.kg_per_batch
                elif recipe.percentage and recipe.percentage > 0:
                    needed_kg = total_req_kg * (recipe.percentage / 100)
                else:
                    continue  # Skip if no valid quantity specified
                
                if needed_kg <= 0:
                    continue
                
                # Categorize by component type
                if component_item.item_type and component_item.item_type.type_name == 'WIPF':
                    filling_needs[component_item.id] = filling_needs.get(component_item.id, 0) + needed_kg
                    logger.info(f"WIPF requirement: {component_item.item_code} needs {needed_kg} kg")
                elif component_item.item_type and component_item.item_type.type_name == 'WIP':
                    production_needs[component_item.id] = production_needs.get(component_item.id, 0) + needed_kg
                    logger.info(f"WIP requirement: {component_item.item_code} needs {needed_kg} kg")

        # Step 3: Update Filling Table
        logger.info(f"Updating Filling requirements: {len(filling_needs)} items")
        
        # Delete existing entries for the day to ensure clean slate
        deleted_filling = Filling.query.filter_by(
            filling_date=packing_date, 
            week_commencing=week_commencing
        ).delete()
        logger.info(f"Deleted {deleted_filling} existing filling entries")
        
        filling_created = 0
        for item_id, total_kg in filling_needs.items():
            if total_kg > 0:
                new_filling = Filling(
                    filling_date=packing_date,
                    week_commencing=week_commencing,
                    item_id=item_id,
                    kilo_per_size=total_kg
                )
                db.session.add(new_filling)
                filling_created += 1
                
                item = ItemMaster.query.get(item_id)
                logger.info(f"Created filling entry: {item.item_code if item else item_id} - {total_kg} kg")

        # Step 4: Update Production Table
        logger.info(f"Updating Production requirements: {len(production_needs)} items")
        
        # Delete existing entries for the day
        deleted_production = Production.query.filter_by(
            production_date=packing_date, 
            week_commencing=week_commencing
        ).delete()
        logger.info(f"Deleted {deleted_production} existing production entries")
        
        production_created = 0
        for item_id, total_kg in production_needs.items():
            if total_kg > 0:
                # Assuming 100kg batch size - this could be made configurable
                batches = total_kg / 100
                
                item = ItemMaster.query.get(item_id)
                production_code = item.item_code if item else str(item_id)
                description = item.description if item else f"Production for item {item_id}"
                
                new_production = Production(
                    production_date=packing_date,
                    week_commencing=week_commencing,
                    item_id=item_id,
                    production_code=production_code,
                    description=description,
                    total_kg=total_kg,
                    batches=batches
                )
                db.session.add(new_production)
                production_created += 1
                
                logger.info(f"Created production entry: {production_code} - {total_kg} kg ({batches} batches)")

        # Step 5: Recursive explosion for WIP requirements
        # WIP items might also need other WIP/RM components
        if production_needs:
            logger.info("Processing recursive requirements for WIP items")
            for wip_item_id, required_kg in production_needs.items():
                # Get recipes for this WIP item
                wip_recipe_components = RecipeMaster.query.filter_by(
                    finished_good_id=wip_item_id
                ).join(ItemMaster, RecipeMaster.raw_material_id == ItemMaster.id).all()
                
                for recipe in wip_recipe_components:
                    component_item = recipe.raw_material_item
                    if not component_item:
                        continue
                    
                    # Calculate component requirement
                    if recipe.kg_per_batch and recipe.kg_per_batch > 0:
                        needed_kg = required_kg * recipe.kg_per_batch
                    elif recipe.percentage and recipe.percentage > 0:
                        needed_kg = required_kg * (recipe.percentage / 100)
                    else:
                        continue
                    
                    if needed_kg <= 0:
                        continue
                    
                    # Only create additional production entries for WIP components
                    if (component_item.item_type and 
                        component_item.item_type.type_name == 'WIP' and 
                        component_item.id not in production_needs):
                        
                        additional_batches = needed_kg / 100
                        additional_production = Production(
                            production_date=packing_date,
                            week_commencing=week_commencing,
                            item_id=component_item.id,
                            production_code=component_item.item_code,
                            description=component_item.description,
                            total_kg=needed_kg,
                            batches=additional_batches
                        )
                        db.session.add(additional_production)
                        production_created += 1
                        logger.info(f"Created recursive production entry: {component_item.item_code} - {needed_kg} kg")

        # Commit all changes
        db.session.commit()
        
        summary = f"Recipe explosion completed: {filling_created} filling entries, {production_created} production entries created"
        logger.info(summary)
        return True, summary
        
    except Exception as e:
        db.session.rollback()
        error_msg = f"Recipe explosion failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg

def get_recipe_summary(item_id):
    """
    Get a summary of recipe explosion for a specific item
    Useful for debugging and verification
    """
    try:
        item = ItemMaster.query.get(item_id)
        if not item:
            return None, "Item not found"
        
        # Get all recipe components for this item
        recipe_components = RecipeMaster.query.filter_by(
            finished_good_id=item_id
        ).join(ItemMaster, RecipeMaster.raw_material_id == ItemMaster.id).all()
        
        summary = {
            'item': {
                'code': item.item_code,
                'description': item.description,
                'type': item.item_type.type_name if item.item_type else 'Unknown'
            },
            'components': [],
            'by_type': {'RM': 0, 'WIP': 0, 'WIPF': 0},
            'total_components': len(recipe_components)
        }
        
        for recipe in recipe_components:
            component_item = recipe.raw_material_item
            if component_item:
                comp_info = {
                    'code': component_item.item_code,
                    'description': component_item.description,
                    'type': component_item.item_type.type_name if component_item.item_type else 'Unknown',
                    'kg_per_batch': recipe.kg_per_batch,
                    'percentage': recipe.percentage
                }
                summary['components'].append(comp_info)
                
                # Count by type
                comp_type = component_item.item_type.type_name if component_item.item_type else 'Unknown'
                summary['by_type'][comp_type] = summary['by_type'].get(comp_type, 0) + 1
        
        return summary, "Success"
        
    except Exception as e:
        return None, f"Error generating recipe summary: {str(e)}"

def calculate_component_requirements(item_id, required_kg):
    """
    Calculate all component requirements for a specific item and quantity
    Uses existing RecipeMaster structure
    """
    try:
        requirements = {}
        
        # Get direct recipe components
        recipe_components = RecipeMaster.query.filter_by(
            finished_good_id=item_id
        ).join(ItemMaster, RecipeMaster.raw_material_id == ItemMaster.id).all()
        
        for recipe in recipe_components:
            component_item = recipe.raw_material_item
            if not component_item:
                continue
            
            # Calculate requirement
            if recipe.kg_per_batch and recipe.kg_per_batch > 0:
                needed_kg = required_kg * recipe.kg_per_batch
            elif recipe.percentage and recipe.percentage > 0:
                needed_kg = required_kg * (recipe.percentage / 100)
            else:
                continue
            
            if needed_kg > 0:
                requirements[component_item.item_code] = {
                    'item': component_item,
                    'total_kg': needed_kg,
                    'type': component_item.item_type.type_name if component_item.item_type else 'Unknown',
                    'recipe_kg_per_batch': recipe.kg_per_batch,
                    'recipe_percentage': recipe.percentage
                }
        
        return requirements, "Success"
        
    except Exception as e:
        return None, f"Error calculating requirements: {str(e)}" 