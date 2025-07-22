"""
Enhanced BOM (Bill of Materials) Service
======================================

This service provides optimized BOM calculations using the item_master
hierarchy fields (wip_item_id, wipf_item_id) for managing production requirements,
recipe explosions, sand inventory calculations.
"""

from flask import jsonify
from database import db
from models import ItemMaster, Recipe, RecipeDetail, Production, ProductionDetail, Packing, PackingDetail
from models.filling import Filling  
from models.production import Production
from models.item_master import ItemMaster
from models.recipe_master import RecipeMaster
from models.item_type import ItemType
from models.soh import SOH
from models.usage_report_table import UsageReportTable
from models.usage_report_table import UsageReportTable
from models.raw_material_report_table import RawMaterialReportTable
from models.department import Department
from models.machinery import Machinery
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
import logging
import json

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
    def update_downstream_requirements(week_commencing):
        """Update downstream requirements based on packing entries for an entire week."""
        try:
            from app import db
            from models.packing import Packing
            from models.filling import Filling
            from models.production import Production
            
            logger.info(f"Starting downstream requirement update for week: {week_commencing}")

            # Get all packing entries for the entire week
            packing_entries = Packing.query.filter_by(week_commencing=week_commencing).all()
            
            if not packing_entries:
                logger.warning(f"No packing entries found for week {week_commencing}. Clearing downstream entries.")
                Filling.query.filter_by(week_commencing=week_commencing).delete()
                Production.query.filter_by(week_commencing=week_commencing).delete()
                db.session.commit()
                return True

            wipf_aggregations = {}
            wip_aggregations = {}

            # First pass: Aggregate requirements
            for packing in packing_entries:
                if not packing.item:
                    continue

                if packing.item.wipf_item:
                    wipf_id = packing.item.wipf_item.id
                    if wipf_id not in wipf_aggregations:
                        wipf_aggregations[wipf_id] = {'total_kg': 0, 'item': packing.item.wipf_item}
                    wipf_aggregations[wipf_id]['total_kg'] += packing.requirement_kg

                if packing.item.wip_item:
                    wip_id = packing.item.wip_item.id
                    if wip_id not in wip_aggregations:
                        wip_aggregations[wip_id] = {'total_kg': 0, 'item': packing.item.wip_item}
                    wip_aggregations[wip_id]['total_kg'] += packing.requirement_kg

            # Log aggregations
            logger.info(f"WIPF aggregations for week {week_commencing}: { {data['item'].item_code: data['total_kg'] for data in wipf_aggregations.values()} }")
            logger.info(f"WIP aggregations for week {week_commencing}: { {data['item'].item_code: data['total_kg'] for data in wip_aggregations.values()} }")

            # Clear existing downstream entries for the week before creating new ones
            Filling.query.filter_by(week_commencing=week_commencing).delete()
            # DON'T delete Production entries - we need to preserve planned values
            # Production.query.filter_by(week_commencing=week_commencing).delete()
            logger.info(f"Cleared existing Filling entries for week {week_commencing}")

            # Second pass: Create new Filling entries
            for wipf_id, data in wipf_aggregations.items():
                new_filling = Filling(
                    filling_date=week_commencing,
                    week_commencing=week_commencing,
                    item_id=wipf_id,
                    requirement_kg=data['total_kg'],
                    kilo_per_size=data['total_kg']
                )
                db.session.add(new_filling)
                logger.info(f"Created Filling entry for {data['item'].item_code} with {data['total_kg']} kg")

            # Third pass: Update or create Production entries (preserve planned values)
            for wip_id, data in wip_aggregations.items():
                # Check for existing production entry
                existing_production = Production.query.filter_by(
                    item_id=wip_id,
                    week_commencing=week_commencing
                ).first()
                
                if existing_production:
                    # Update existing entry - preserve all planned values
                    existing_production.total_kg = data['total_kg']
                    existing_production.batches = data['total_kg'] / 300.0
                    existing_production.production_code = data['item'].item_code
                    existing_production.production_date = week_commencing
                    logger.info(f"Updated existing Production entry for {data['item'].item_code} with {data['total_kg']} kg (preserved planned values)")
                else:
                    # Create new entry only if none exists
                    new_production = Production(
                        production_date=week_commencing,
                        week_commencing=week_commencing,
                        item_id=wip_id,
                        production_code=data['item'].item_code,
                        total_kg=data['total_kg'],
                        batches=data['total_kg'] / 300.0
                    )
                    db.session.add(new_production)
                    logger.info(f"Created new Production entry for {data['item'].item_code} with {data['total_kg']} kg")

            db.session.commit()
            
            # Update inventory daily requirements based on the updated production data
            try:
                from controllers.production_controller import update_inventory_daily_requirements
                update_inventory_daily_requirements(week_commencing)
                logger.info(f"Updated inventory daily requirements for week {week_commencing}")
            except Exception as inv_error:
                logger.warning(f"Could not update inventory daily requirements: {inv_error}")
            
            logger.info(f"Successfully updated downstream requirements for week {week_commencing}")
            return True

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in update_downstream_requirements for week {week_commencing}: {e}", exc_info=True)
            return False

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
            'usage_reports_created': 0,
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
                                filling_entry = BOMService._create_filling_entry_from_requirements(soh_record, requirements['filling'])
                                if filling_entry:
                                    results['filling_created'] += 1
                                    # Create usage reports for filling components
                                    for recipe in requirements['filling'].get('recipes', []):
                                        BOMService._create_usage_report(
                                            soh_record,
                                            recipe['raw_material_code'],
                                            recipe['quantity_required']
                                        )
                                        results['usage_reports_created'] += 1
                                
                            if 'production' in requirements:
                                prod_entry = BOMService._create_production_entry_from_requirements(soh_record, requirements['production'])
                                if prod_entry:
                                    results['production_created'] += 1
                                    # Create usage reports for production components
                                    for recipe in requirements['production'].get('recipes', []):
                                        BOMService._create_usage_report(
                                            soh_record,
                                            recipe['raw_material_code'],
                                            recipe['quantity_required']
                                        )
                                        results['usage_reports_created'] += 1
                    
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
        entry = Packing(
            item_id=soh_record.item_id,
            requirement_kg=soh_record.current_stock,
            requirement_unit=soh_record.current_stock,  # Using requirement_unit (singular)
            week_commencing=soh_record.week_commencing,
            packing_date=soh_record.week_commencing
        )
        db.session.add(entry)
        return entry

    @staticmethod
    def _create_packing_entry_from_requirements(soh_record, packing_req):
        """Create a packing entry from calculated requirements"""
        entry = Packing(
            item_id=soh_record.item_id,
            requirement_kg=packing_req['requirement_kg'],
            requirement_unit=packing_req['requirement_unit'],  # Using requirement_unit (singular)
            week_commencing=soh_record.week_commencing,
            packing_date=soh_record.week_commencing
        )
        db.session.add(entry)
        return entry

    @staticmethod
    def _create_filling_entry_from_requirements(soh_record, filling_req):
        """Create a filling entry from calculated requirements"""
        item = ItemMaster.query.filter_by(item_code=filling_req['item_code']).first()
        if not item:
            return None
            
        entry = Filling(
            item_id=item.id,
            requirement_kg=filling_req['requirement_kg'],
            kilo_per_size=filling_req['requirement_kg'],
            week_commencing=soh_record.week_commencing,
            filling_date=soh_record.week_commencing
        )
        db.session.add(entry)
        return entry

    @staticmethod
    def _create_production_entry_from_requirements(soh_record, production_req):
        """Create a production entry from calculated requirements"""
        item = ItemMaster.query.filter_by(item_code=production_req['item_code']).first()
        if not item:
            return None
            
        batches = production_req['requirement_kg'] / 300.0 if production_req['requirement_kg'] > 0 else 0.0
        entry = Production(
            item_id=item.id,
            total_kg=production_req['requirement_kg'],
            requirement_kg=production_req['requirement_kg'],
            batches=batches,
            week_commencing=soh_record.week_commencing,
            production_date=soh_record.week_commencing,
            production_code=item.item_code,  # Set production_code from item
            description=item.description  # Set description from item
        )
        db.session.add(entry)
        return entry

    @staticmethod
    def _create_usage_report(soh_record, raw_material_code, quantity_required):
        """Create a usage report entry for a raw material"""
        item = ItemMaster.query.filter_by(item_code=raw_material_code).first()
        if not item:
            return None
            
        entry = UsageReportTable(
            item_id=item.id,
            requirement_kg=quantity_required,
            week_commencing=soh_record.week_commencing,
            usage_date=soh_record.week_commencing
        )
        db.session.add(entry)
        return entry

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

    @staticmethod
    def create_filling_entry(item_id, week_commencing, requirement_kg, requirement_unit):
        """Create or update filling entry for WIPF"""
        try:
            # Get the FG item and its WIPF
            fg_item = ItemMaster.query.get(item_id)
            if not fg_item:
                logger.warning(f"FG item {item_id} not found")
                return None
                
            if not fg_item.wipf_item:
                logger.info(f"No WIPF item relationship for {fg_item.item_code}")
                return None

            # Get all packing entries for this FG and week to calculate total requirement
            total_requirement_kg = db.session.query(func.sum(Packing.requirement_kg)).filter(
                Packing.item_id == item_id,
                Packing.week_commencing == week_commencing
            ).scalar() or 0.0

            # Check for existing filling entry for this WIPF and week
            existing_filling = Filling.query.filter_by(
                item_id=fg_item.wipf_item.id,
                week_commencing=week_commencing,
                filling_date=week_commencing
            ).first()

            if existing_filling:
                # Update existing entry with total requirement from all packing entries
                existing_filling.requirement_kg = total_requirement_kg
                existing_filling.kilo_per_size = total_requirement_kg
                logger.info(f"Updated existing filling entry {existing_filling.id} for WIPF {fg_item.wipf_item.item_code} to {existing_filling.requirement_kg} kg")
                return existing_filling
            else:
                # Create new entry
                new_filling = Filling(
                    filling_date=week_commencing,
                    week_commencing=week_commencing,
                    item_id=fg_item.wipf_item.id,
                    requirement_kg=total_requirement_kg,
                    kilo_per_size=total_requirement_kg
                )
                db.session.add(new_filling)
                logger.info(f"Created new filling entry for WIPF {fg_item.wipf_item.item_code} ({total_requirement_kg} kg)")
                return new_filling

        except Exception as e:
            logger.error(f"Error creating filling entry: {str(e)}")
            return None

    @staticmethod
    def create_production_entry(item_id, week_commencing, requirement_kg, requirement_unit):
        """Create or update production entry for WIP"""
        try:
            # Get the FG item and its WIP
            fg_item = ItemMaster.query.get(item_id)
            if not fg_item:
                logger.warning(f"FG item {item_id} not found")
                return None
                
            if not fg_item.wip_item:
                logger.info(f"No WIP item relationship for {fg_item.item_code}")
                return None

            # Get all packing entries for this FG and week to calculate total requirement
            total_requirement_kg = db.session.query(func.sum(Packing.requirement_kg)).filter(
                Packing.item_id == item_id,
                Packing.week_commencing == week_commencing
            ).scalar() or 0.0

            # Check for existing production entry for this WIP and week
            existing_production = Production.query.filter_by(
                item_id=fg_item.wip_item.id,
                week_commencing=week_commencing,
                production_date=week_commencing
            ).first()

            if existing_production:
                # Update existing entry with total requirement from all packing entries
                existing_production.total_kg = total_requirement_kg
                existing_production.batches = total_requirement_kg / 300.0  # Recalculate batches based on new total
                logger.info(f"Updated existing production entry {existing_production.id} for WIP {fg_item.wip_item.item_code} to {existing_production.total_kg} kg")
                return existing_production
            else:
                # Create new entry
                new_production = Production(
                    production_date=week_commencing,
                    week_commencing=week_commencing,
                    item_id=fg_item.wip_item.id,
                    production_code=fg_item.wip_item.item_code,
                    description=fg_item.wip_item.description,
                    total_kg=total_requirement_kg,
                    batches=total_requirement_kg / 300.0  # Calculate batches as Total KG/300
                )
                db.session.add(new_production)
                logger.info(f"Created new production entry for WIP {fg_item.wip_item.item_code} ({total_requirement_kg} kg)")
                return new_production

        except Exception as e:
            logger.error(f"Error creating production entry: {str(e)}")
            return None

    @staticmethod
    def create_usage_report(item_id, week_commencing, requirement_kg, requirement_unit):
        """Create usage report entries for raw materials"""
        try:
            # Get the FG item and its WIP
            fg_item = ItemMaster.query.get(item_id)
            if not fg_item or not fg_item.wip_item:
                return None

            # Get recipe components for the WIP
            recipe_components = RecipeMaster.query.filter_by(
                recipe_wip_id=fg_item.wip_item.id
            ).all()

            if not recipe_components:
                return None

            # Calculate total recipe quantity
            total_recipe_qty = sum(float(r.quantity_kg or 0) for r in recipe_components)
            if total_recipe_qty <= 0:
                return None

            usage_reports = []
            for recipe in recipe_components:
                if not recipe.component_item:
                    continue

                # Calculate usage and percentage
                usage_kg = (float(recipe.quantity_kg) / total_recipe_qty) * requirement_kg
                percentage = (float(recipe.quantity_kg) / total_recipe_qty) * 100

                # Check for existing usage report
                existing_usage = UsageReportTable.query.filter_by(
                    week_commencing=week_commencing,
                    production_date=week_commencing,
                    recipe_code=fg_item.wip_item.item_code,
                    raw_material=recipe.component_item.description
                ).first()

                if existing_usage:
                    # Update existing entry
                    existing_usage.usage_kg += usage_kg
                    existing_usage.percentage = percentage
                    usage_reports.append(existing_usage)
                else:
                    # Create new usage report
                    new_usage = UsageReportTable(
                        week_commencing=week_commencing,
                        production_date=week_commencing,
                        recipe_code=fg_item.wip_item.item_code,
                        raw_material=recipe.component_item.description,
                        usage_kg=usage_kg,
                        percentage=percentage
                    )
                    db.session.add(new_usage)
                    usage_reports.append(new_usage)

                # Create/update raw material report
                existing_raw = RawMaterialReportTable.query.filter_by(
                    week_commencing=week_commencing,
                    production_date=week_commencing,
                    raw_material_id=recipe.component_item.id
                ).first()

                if existing_raw:
                    existing_raw.meat_required += usage_kg
                else:
                    new_raw = RawMaterialReportTable(
                        week_commencing=week_commencing,
                        production_date=week_commencing,
                        raw_material_id=recipe.component_item.id,
                        raw_material=recipe.component_item.description,
                        meat_required=usage_kg
                    )
                    db.session.add(new_raw)

            return usage_reports

        except Exception as e:
            logger.error(f"Error creating usage report: {str(e)}")
            return None

    @staticmethod
    def verify_totals(week_commencing):
        """Verify that packing and production totals match for a given week"""
        try:
            from app import db
            from sqlalchemy import func
            from models.packing import Packing
            from models.filling import Filling
            from models.production import Production
            
            # Get total packing requirements for the week
            packing_totals = {}  # Key: wip_item_id, Value: total_kg
            packing_entries = Packing.query.filter_by(week_commencing=week_commencing).all()
            
            for packing in packing_entries:
                if not packing.item or not packing.item.wip_item:
                    continue
                    
                wip_id = packing.item.wip_item.id
                if wip_id not in packing_totals:
                    packing_totals[wip_id] = {
                        'total_kg': 0,
                        'wip_code': packing.item.wip_item.item_code,
                        'fg_codes': set()
                    }
                packing_totals[wip_id]['total_kg'] += packing.requirement_kg
                packing_totals[wip_id]['fg_codes'].add(packing.item.item_code)
            
            # Get production totals for the week
            production_entries = Production.query.filter_by(week_commencing=week_commencing).all()
            
            mismatches = []
            for wip_id, packing_data in packing_totals.items():
                production = next((p for p in production_entries if p.item_id == wip_id), None)
                if not production:
                    mismatches.append({
                        'wip_code': packing_data['wip_code'],
                        'packing_total': packing_data['total_kg'],
                        'production_total': 0,
                        'fg_codes': list(packing_data['fg_codes']),
                        'error': 'Missing production entry'
                    })
                elif abs(production.total_kg - packing_data['total_kg']) > 0.01:  # Allow small rounding differences
                    mismatches.append({
                        'wip_code': packing_data['wip_code'],
                        'packing_total': packing_data['total_kg'],
                        'production_total': production.total_kg,
                        'fg_codes': list(packing_data['fg_codes']),
                        'error': 'Total mismatch'
                    })
            
            return {
                'success': len(mismatches) == 0,
                'mismatches': mismatches
            }
            
        except Exception as e:
            logger.error(f"Error verifying totals: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }