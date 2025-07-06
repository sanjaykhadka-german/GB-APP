"""
Enhanced BOM (Bill of Materials) Service
======================================

This service provides optimized BOM calculations using the item_master
hierarchy fields (wip_item_id, wipf_item_id) for managing production requirements,
recipe explosions, and inventory calculations.
"""

from app import db
from models.packing import Packing
from models.filling import Filling  
from models.production import Production
from models.item_master import ItemMaster
from models.recipe_master import RecipeMaster
from models.item_type import ItemType
from models.soh import SOH
import logging

logger = logging.getLogger(__name__)

class BOMService:
    """Unified BOM service combining core and enhanced functionality"""
    
    @staticmethod
    def get_fg_hierarchy(fg_code):
        """Get the complete hierarchy for a finished good using item_master"""
        fg_item = db.session.query(ItemMaster).join(ItemType).filter(
            ItemMaster.item_code == fg_code,
            ItemType.type_name == 'FG'
        ).first()
        
        if not fg_item:
            return None
            
        hierarchy = {
            'fg_code': fg_item.item_code,
            'fg_description': fg_item.description,
            'filling_code': None,
            'filling_description': None,
            'production_code': None,
            'production_description': None,
            'calculation_factor': fg_item.calculation_factor or 1.0,
            'flow_type': 'Direct production (FG only)'
        }
        
        # Get WIP item if exists
        if fg_item.wip_item:
            hierarchy['production_code'] = fg_item.wip_item.item_code
            hierarchy['production_description'] = fg_item.wip_item.description
            
        # Get WIPF item if exists
        if fg_item.wipf_item:
            hierarchy['filling_code'] = fg_item.wipf_item.item_code
            hierarchy['filling_description'] = fg_item.wipf_item.description
            
        # Determine flow type
        if hierarchy['filling_code'] and hierarchy['production_code']:
            hierarchy['flow_type'] = 'Complex flow (RM -> WIP -> WIPF -> FG)'
        elif hierarchy['filling_code']:
            hierarchy['flow_type'] = 'Filling flow (RM -> WIPF -> FG)'
        elif hierarchy['production_code']:
            hierarchy['flow_type'] = 'Production flow (RM -> WIP -> FG)'
            
        return hierarchy

    @staticmethod
    def get_all_fg_hierarchies():
        """Get all active FG hierarchies for bulk processing"""
        fg_items = db.session.query(ItemMaster).join(ItemType).filter(
            ItemType.type_name == 'FG'
        ).all()
        
        hierarchies = []
        for fg in fg_items:
            hierarchy = {
                'fg_code': fg.item_code,
                'filling_code': fg.wipf_item.item_code if fg.wipf_item else None,
                'production_code': fg.wip_item.item_code if fg.wip_item else None,
                'calculation_factor': fg.calculation_factor or 1.0,
                'flow_type': 'Direct production (FG only)'
            }
            
            # Determine flow type
            if hierarchy['filling_code'] and hierarchy['production_code']:
                hierarchy['flow_type'] = 'Complex flow (RM -> WIP -> WIPF -> FG)'
            elif hierarchy['filling_code']:
                hierarchy['flow_type'] = 'Filling flow (RM -> WIPF -> FG)'
            elif hierarchy['production_code']:
                hierarchy['flow_type'] = 'Production flow (RM -> WIP -> FG)'
                
            hierarchies.append(hierarchy)
            
        return hierarchies

    @staticmethod
    def update_downstream_requirements(packing_date, week_commencing):
        """
        Aggregates all packing requirements for a given day and updates/creates
        the corresponding Production and Filling plans. This is the "Recipe Explosion".
        
        Args:
            packing_date: Date for which to calculate requirements
            week_commencing: Week commencing date for planning period
        """
        try:
            logger.info(f"Starting recipe explosion for {packing_date}, week {week_commencing}")
            
            # Clear existing production and filling entries for this date
            Production.query.filter_by(
                production_date=packing_date,
                week_commencing=week_commencing
            ).delete()
            
            Filling.query.filter_by(
                filling_date=packing_date,
                week_commencing=week_commencing
            ).delete()
            
            db.session.commit()
            logger.info("Cleared existing production and filling entries")
            
            # Step 1: Get all packing entries for the date
            packing_entries = Packing.query.filter_by(
                packing_date=packing_date,
                week_commencing=week_commencing
            ).all()
            
            logger.info(f"Found {len(packing_entries)} packing entries")
            
            # Initialize dictionaries to track requirements
            production_needs = {}  # WIP item ID -> total kg needed
            filling_needs = {}     # WIPF item ID -> total kg needed
            
            # Step 2: Calculate requirements for each packing entry
            for packing in packing_entries:
                fg_item = packing.item
                
                if not fg_item:
                    logger.warning(f"Packing entry {packing.id} has no associated item")
                    continue
                    
                logger.info(f"Processing FG item: {fg_item.item_code} with requirement {packing.requirement_kg}kg")
                
                # Get hierarchy information
                hierarchy = BOMService.get_fg_hierarchy(fg_item.item_code)
                if not hierarchy:
                    logger.warning(f"No hierarchy found for FG {fg_item.item_code}")
                    continue

                # Calculate required kg based on packing requirement and calculation factor
                base_required_kg = packing.requirement_kg or 0
                factor = hierarchy['calculation_factor']
                required_kg = base_required_kg * factor
                
                # Handle WIP requirements if exists
                if hierarchy['production_code']:
                    wip_item = fg_item.wip_item
                    if wip_item:
                        wip_loss = wip_item.loss_percentage or 0
                        wip_required = required_kg * (1 + (wip_loss / 100))
                        
                        if wip_item.id not in production_needs:
                            production_needs[wip_item.id] = 0
                        production_needs[wip_item.id] += wip_required
                        logger.info(f"Added {wip_required}kg to WIP {wip_item.item_code} (with {wip_loss}% loss)")
                
                # Handle WIPF requirements if exists
                if hierarchy['filling_code']:
                    wipf_item = fg_item.wipf_item
                    if wipf_item:
                        wipf_loss = wipf_item.loss_percentage or 0
                        wipf_required = required_kg * (1 + (wipf_loss / 100))
                        
                        if wipf_item.id not in filling_needs:
                            filling_needs[wipf_item.id] = 0
                        filling_needs[wipf_item.id] += wipf_required
                        logger.info(f"Added {wipf_required}kg to WIPF {wipf_item.item_code} (with {wipf_loss}% loss)")
            
            logger.info(f"Production needs: {production_needs}")
            logger.info(f"Filling needs: {filling_needs}")
            
            # Step 3: Create or update Production entries
            for wip_id, total_kg in production_needs.items():
                # Calculate batches (300kg per batch)
                batches = total_kg / 300.0 if total_kg > 0 else 0.0
                
                existing_prod = Production.query.filter_by(
                    production_date=packing_date,
                    week_commencing=week_commencing,
                    item_id=wip_id
                ).first()
                
                if existing_prod:
                    existing_prod.total_kg = total_kg
                    existing_prod.requirement_kg = total_kg
                    existing_prod.batches = batches
                    logger.info(f"Updated Production entry for WIP {wip_id}: {total_kg}kg ({batches:.2f} batches)")
                else:
                    wip_item = ItemMaster.query.get(wip_id)
                    new_prod = Production(
                        production_date=packing_date,
                        week_commencing=week_commencing,
                        item_id=wip_id,
                        total_kg=total_kg,
                        requirement_kg=total_kg,
                        production_code=wip_item.item_code if wip_item else None,
                        description=wip_item.description if wip_item else None,
                        batches=batches
                    )
                    db.session.add(new_prod)
                    logger.info(f"Created Production entry for WIP {wip_id}: {total_kg}kg ({batches:.2f} batches)")
            
            # Step 4: Create or update Filling entries
            for wipf_id, total_kg in filling_needs.items():
                existing_fill = Filling.query.filter_by(
                    filling_date=packing_date,
                    week_commencing=week_commencing,
                    item_id=wipf_id
                ).first()
                
                if existing_fill:
                    existing_fill.requirement_kg = total_kg
                    existing_fill.kilo_per_size = total_kg
                    logger.info(f"Updated Filling entry for WIPF {wipf_id}: {total_kg}kg")
                else:
                    new_fill = Filling(
                        filling_date=packing_date,
                        week_commencing=week_commencing,
                        item_id=wipf_id,
                        requirement_kg=total_kg,
                        kilo_per_size=total_kg
                    )
                    db.session.add(new_fill)
                    logger.info(f"Created Filling entry for WIPF {wipf_id}: {total_kg}kg")
            
            db.session.commit()
            logger.info("Successfully updated downstream requirements")
            return True, "Successfully updated downstream requirements"
            
        except Exception as e:
            logger.error(f"Error updating downstream requirements: {str(e)}")
            db.session.rollback()
            raise

    @staticmethod
    def calculate_downstream_requirements(fg_code, fg_quantity):
        """
        Calculate downstream requirements for FG using item_master hierarchy
        Returns: dict with packing, filling, and production requirements
        """
        hierarchy = BOMService.get_fg_hierarchy(fg_code)
        if not hierarchy:
            logger.warning(f"No hierarchy found for FG {fg_code}")
            return None
        
        factor = hierarchy['calculation_factor']
        adjusted_quantity = fg_quantity * factor
        
        requirements = {
            'fg_code': fg_code,
            'fg_quantity': fg_quantity,
            'adjusted_quantity': adjusted_quantity,
            'calculation_factor': factor,
            'flow_type': hierarchy['flow_type']
        }
        
        # Calculate packing requirements (always needed)
        fg_item = ItemMaster.query.filter_by(item_code=fg_code).first()
        if fg_item:
            requirements['packing'] = {
                'item_code': fg_code,
                'description': fg_item.description,
                'requirement_kg': adjusted_quantity,
                'requirement_unit': adjusted_quantity / (fg_item.avg_weight_per_unit or 1)
            }
        
        # Calculate filling requirements if WIPF exists
        if hierarchy['filling_code']:
            wipf_item = ItemMaster.query.filter_by(item_code=hierarchy['filling_code']).first()
            if wipf_item:
                filling_recipes = RecipeMaster.query.filter_by(recipe_wip_id=wipf_item.id).all()
                
                requirements['filling'] = {
                    'item_code': hierarchy['filling_code'],
                    'description': hierarchy['filling_description'],
                    'requirement_kg': adjusted_quantity,
                    'requirement_unit': adjusted_quantity,
                    'recipes': [
                        {
                            'raw_material_code': ItemMaster.query.get(r.component_item_id).item_code,
                            'quantity_required': float(r.quantity_kg) * adjusted_quantity
                        }
                        for r in filling_recipes
                    ]
                }
        
        # Calculate production requirements if WIP exists
        if hierarchy['production_code']:
            wip_item = ItemMaster.query.filter_by(item_code=hierarchy['production_code']).first()
            if wip_item:
                production_recipes = RecipeMaster.query.filter_by(recipe_wip_id=wip_item.id).all()
                
                requirements['production'] = {
                    'item_code': hierarchy['production_code'],
                    'description': hierarchy['production_description'],
                    'requirement_kg': adjusted_quantity,
                    'requirement_unit': adjusted_quantity,
                    'recipes': [
                        {
                            'raw_material_code': ItemMaster.query.get(r.component_item_id).item_code,
                            'quantity_required': float(r.quantity_kg) * adjusted_quantity
                        }
                        for r in production_recipes
                    ]
                }
        
        return requirements

    @staticmethod
    def process_soh_upload(soh_records):
        """Process SOH upload using BOM calculations with item_master hierarchy"""
        results = {
            'processed': 0,
            'packing_created': 0,
            'filling_created': 0,
            'production_created': 0,
            'errors': []
        }
        
        try:
            # Get all hierarchies at once for efficiency
            fg_hierarchies = {h['fg_code']: h for h in BOMService.get_all_fg_hierarchies()}
            
            for soh_record in soh_records:
                try:
                    fg_code = soh_record.item_code
                    hierarchy = fg_hierarchies.get(fg_code)
                    
                    if not hierarchy or hierarchy['flow_type'] == 'Direct production (FG only)':
                        logger.info(f"No hierarchy defined for {fg_code}, creating packing only")
                        BOMService._create_packing_entry(soh_record)
                        results['packing_created'] += 1
                    else:
                        # Calculate requirements using hierarchy
                        requirements = BOMService.calculate_downstream_requirements(
                            fg_code, soh_record.current_stock
                        )
                        
                        if requirements:
                            if 'packing' in requirements:
                                BOMService._create_packing_entry_from_requirements(soh_record, requirements['packing'])
                                results['packing_created'] += 1
                                
                            if 'filling' in requirements:
                                BOMService._create_filling_entry_from_requirements(soh_record, requirements['filling'])
                                results['filling_created'] += 1
                                
                            if 'production' in requirements:
                                BOMService._create_production_entry_from_requirements(soh_record, requirements['production'])
                                results['production_created'] += 1
                                
                    results['processed'] += 1
                    
                except Exception as e:
                    error_msg = f"Error processing SOH record {soh_record.id}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    
            db.session.commit()
            return results
            
        except Exception as e:
            logger.error(f"Error in SOH upload processing: {str(e)}")
            db.session.rollback()
            raise

    @staticmethod
    def _create_packing_entry(soh_record):
        """Create a basic packing entry from SOH record"""
        return Packing(
            item_id=soh_record.item_id,
            requirement_kg=soh_record.current_stock
        )

    @staticmethod
    def _create_packing_entry_from_requirements(soh_record, packing_req):
        """Create a packing entry from calculated requirements"""
        return Packing(
            item_id=soh_record.item_id,
            requirement_kg=packing_req['requirement_kg'],
            requirement_unit=packing_req['requirement_unit']
        )

    @staticmethod
    def _create_filling_entry_from_requirements(soh_record, filling_req):
        """Create a filling entry from calculated requirements"""
        return Filling(
            item_id=ItemMaster.query.filter_by(item_code=filling_req['item_code']).first().id,
            requirement_kg=filling_req['requirement_kg'],
            kilo_per_size=filling_req['requirement_kg']
        )

    @staticmethod
    def _create_production_entry_from_requirements(soh_record, production_req):
        """Create a production entry from calculated requirements"""
        batches = production_req['requirement_kg'] / 300.0 if production_req['requirement_kg'] > 0 else 0.0
        return Production(
            item_id=ItemMaster.query.filter_by(item_code=production_req['item_code']).first().id,
            total_kg=production_req['requirement_kg'],
            requirement_kg=production_req['requirement_kg'],
            batches=batches
        )

    @staticmethod
    def get_recipe_summary(item_id):
        """Get a summary of all recipe components for an item"""
        try:
            item = ItemMaster.query.get(item_id)
            if not item:
                return None
                
            result = {
                'code': item.item_code,
                'description': item.description,
                'type': item.item_type.type_name if item.item_type else None,
                'components': []
            }
            
            recipes = RecipeMaster.query.filter_by(finished_good_id=item_id).all()
            for recipe in recipes:
                component_item = recipe.raw_material_item
                if component_item:
                    result['components'].append({
                        'code': component_item.item_code,
                        'description': component_item.description,
                        'type': component_item.item_type.type_name if component_item.item_type else None,
                        'kg_per_batch': recipe.kg_per_batch,
                        'percentage': recipe.percentage
                    })
                    
            return result
        except Exception as e:
            logger.error(f"Error getting recipe summary: {str(e)}")
            return None

    @staticmethod
    def get_bom_explosion_summary(fg_code):
        """Get a complete BOM explosion summary for a finished good"""
        try:
            hierarchy = BOMService.get_fg_hierarchy(fg_code)
            if not hierarchy:
                return None
                
            summary = {
                'fg_code': fg_code,
                'description': hierarchy['fg_description'],
                'flow_type': hierarchy['flow_type'],
                'calculation_factor': hierarchy['calculation_factor'],
                'components': {
                    'production': [],
                    'filling': []
                }
            }
            
            # Get production components if exists
            if hierarchy['production_code']:
                wip_item = ItemMaster.query.filter_by(item_code=hierarchy['production_code']).first()
                if wip_item:
                    recipes = RecipeMaster.query.filter_by(recipe_wip_id=wip_item.id).all()
                    for recipe in recipes:
                        component = ItemMaster.query.get(recipe.component_item_id)
                        if component:
                            summary['components']['production'].append({
                                'code': component.item_code,
                                'description': component.description,
                                'kg_per_batch': recipe.kg_per_batch,
                                'percentage': recipe.percentage
                            })
            
            # Get filling components if exists
            if hierarchy['filling_code']:
                wipf_item = ItemMaster.query.filter_by(item_code=hierarchy['filling_code']).first()
                if wipf_item:
                    recipes = RecipeMaster.query.filter_by(recipe_wip_id=wipf_item.id).all()
                    for recipe in recipes:
                        component = ItemMaster.query.get(recipe.component_item_id)
                        if component:
                            summary['components']['filling'].append({
                                'code': component.item_code,
                                'description': component.description,
                                'kg_per_batch': recipe.kg_per_batch,
                                'percentage': recipe.percentage
                            })
            
            return summary
        except Exception as e:
            logger.error(f"Error getting BOM explosion summary: {str(e)}")
            return None 