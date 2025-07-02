#!/usr/bin/env python3
"""
Enhanced BOM Service with Joining Table Integration
==================================================

This service provides optimized BOM calculations using the joining table
for FG → WIPF → WIP relationships, dramatically improving performance.
"""

from models.joining import Joining
from models.item_master import ItemMaster
from models.recipe_master import RecipeMaster
from models.soh import SOH
from models.packing import Packing
from models.filling import Filling
from models.production import Production
from database import db
from sqlalchemy import and_, or_
import logging

logger = logging.getLogger(__name__)

class EnhancedBOMService:
    """Enhanced BOM service using joining table for optimized calculations"""
    
    @staticmethod
    def get_fg_hierarchy(fg_code):
        """Get the complete hierarchy for a finished good using joining table"""
        joining = Joining.get_hierarchy_for_fg(fg_code)
        if joining:
            return {
                'fg_code': joining.fg_code,
                'fg_description': joining.fg_description,
                'filling_code': joining.filling_code,
                'filling_description': joining.filling_description,
                'production_code': joining.production_code,
                'production_description': joining.production_description,
                'calculation_factor': joining.calculation_factor,
                'flow_type': joining.get_manufacturing_flow_type()
            }
        return None
    
    @staticmethod
    def get_all_fg_hierarchies():
        """Get all active FG hierarchies for bulk processing"""
        joinings = Joining.get_all_fg_hierarchies()
        return [
            {
                'fg_code': j.fg_code,
                'filling_code': j.filling_code,
                'production_code': j.production_code,
                'calculation_factor': j.calculation_factor,
                'flow_type': j.get_manufacturing_flow_type()
            }
            for j in joinings
        ]
    
    @staticmethod
    def calculate_downstream_requirements(fg_code, fg_quantity):
        """
        Calculate downstream requirements for FG using joining table
        Returns: dict with packing, filling, and production requirements
        """
        hierarchy = EnhancedBOMService.get_fg_hierarchy(fg_code)
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
            filling_recipes = RecipeMaster.query.filter_by(
                finished_good_id=ItemMaster.query.filter_by(item_code=hierarchy['filling_code']).first().id
            ).all()
            
            requirements['filling'] = {
                'item_code': hierarchy['filling_code'],
                'description': hierarchy['filling_description'],
                'requirement_kg': adjusted_quantity,
                'requirement_unit': adjusted_quantity,
                'recipes': [
                    {
                        'raw_material_code': ItemMaster.query.get(r.raw_material_id).item_code,
                        'quantity_required': r.quantity * adjusted_quantity
                    }
                    for r in filling_recipes
                ]
            }
        
        # Calculate production requirements if WIP exists
        if hierarchy['production_code']:
            production_recipes = RecipeMaster.query.filter_by(
                finished_good_id=ItemMaster.query.filter_by(item_code=hierarchy['production_code']).first().id
            ).all()
            
            requirements['production'] = {
                'item_code': hierarchy['production_code'],
                'description': hierarchy['production_description'],
                'requirement_kg': adjusted_quantity,
                'requirement_unit': adjusted_quantity,
                'recipes': [
                    {
                        'raw_material_code': ItemMaster.query.get(r.raw_material_id).item_code,
                        'quantity_required': r.quantity * adjusted_quantity
                    }
                    for r in production_recipes
                ]
            }
        
        return requirements
    
    @staticmethod
    def process_soh_upload_enhanced(soh_records):
        """
        Process SOH upload using enhanced BOM calculations with joining table
        This is significantly faster than the recursive approach
        """
        results = {
            'processed': 0,
            'packing_created': 0,
            'filling_created': 0,
            'production_created': 0,
            'errors': []
        }
        
        try:
            # Get all hierarchies at once for efficiency
            fg_hierarchies = {h['fg_code']: h for h in EnhancedBOMService.get_all_fg_hierarchies()}
            
            for soh_record in soh_records:
                try:
                    fg_code = soh_record.item_code
                    hierarchy = fg_hierarchies.get(fg_code)
                    
                    if not hierarchy:
                        logger.info(f"No hierarchy defined for {fg_code}, creating packing only")
                        # Create packing entry for direct production
                        EnhancedBOMService._create_packing_entry(soh_record)
                        results['packing_created'] += 1
                    else:
                        # Calculate requirements using hierarchy
                        requirements = EnhancedBOMService.calculate_downstream_requirements(
                            fg_code, soh_record.current_stock
                        )
                        
                        if requirements:
                            # Create packing entry
                            if 'packing' in requirements:
                                EnhancedBOMService._create_packing_entry_from_requirements(
                                    soh_record, requirements['packing']
                                )
                                results['packing_created'] += 1
                            
                            # Create filling entry if needed
                            if 'filling' in requirements:
                                EnhancedBOMService._create_filling_entry_from_requirements(
                                    soh_record, requirements['filling']
                                )
                                results['filling_created'] += 1
                            
                            # Create production entry if needed
                            if 'production' in requirements:
                                EnhancedBOMService._create_production_entry_from_requirements(
                                    soh_record, requirements['production']
                                )
                                results['production_created'] += 1
                    
                    results['processed'] += 1
                    
                except Exception as e:
                    error_msg = f"Error processing {soh_record.item_code}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            # Commit all changes
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            results['errors'].append(f"Database error: {str(e)}")
            logger.error(f"SOH processing failed: {str(e)}")
        
        return results
    
    @staticmethod
    def _create_packing_entry(soh_record):
        """Create a packing entry from SOH record"""
        existing = Packing.query.filter_by(
            item_code=soh_record.item_code,
            week_commencing=soh_record.week_commencing
        ).first()
        
        if existing:
            logger.info(f"Packing entry already exists for {soh_record.item_code}")
            return
        
        fg_item = ItemMaster.query.filter_by(item_code=soh_record.item_code).first()
        if not fg_item:
            logger.warning(f"FG item {soh_record.item_code} not found in ItemMaster")
            return
        
        packing = Packing(
            item_code=soh_record.item_code,
            description=fg_item.description,
            week_commencing=soh_record.week_commencing,
            calculation_factor=soh_record.calculation_factor or 1.0,
            requirement_kg=soh_record.current_stock * (soh_record.calculation_factor or 1.0),
            requirement_unit=soh_record.current_stock * (soh_record.calculation_factor or 1.0) / (fg_item.avg_weight_per_unit or 1)
        )
        
        db.session.add(packing)
        logger.info(f"✓ Packing entry created for {soh_record.item_code}")
    
    @staticmethod
    def _create_packing_entry_from_requirements(soh_record, packing_req):
        """Create packing entry from calculated requirements"""
        existing = Packing.query.filter_by(
            item_code=soh_record.item_code,
            week_commencing=soh_record.week_commencing
        ).first()
        
        if existing:
            return
        
        packing = Packing(
            item_code=packing_req['item_code'],
            description=packing_req['description'],
            week_commencing=soh_record.week_commencing,
            calculation_factor=soh_record.calculation_factor or 1.0,
            requirement_kg=packing_req['requirement_kg'],
            requirement_unit=packing_req['requirement_unit']
        )
        
        db.session.add(packing)
    
    @staticmethod
    def _create_filling_entry_from_requirements(soh_record, filling_req):
        """Create filling entry from calculated requirements"""
        existing = Filling.query.filter_by(
            item_code=filling_req['item_code'],
            week_commencing=soh_record.week_commencing
        ).first()
        
        if existing:
            return
        
        filling = Filling(
            item_code=filling_req['item_code'],
            description=filling_req['description'],
            week_commencing=soh_record.week_commencing,
            calculation_factor=soh_record.calculation_factor or 1.0,
            requirement_kg=filling_req['requirement_kg'],
            requirement_unit=filling_req['requirement_unit']
        )
        
        db.session.add(filling)
    
    @staticmethod
    def _create_production_entry_from_requirements(soh_record, production_req):
        """Create production entry from calculated requirements"""
        existing = Production.query.filter_by(
            item_code=production_req['item_code'],
            week_commencing=soh_record.week_commencing
        ).first()
        
        if existing:
            return
        
        # Get the production item for description
        production_item = ItemMaster.query.filter_by(item_code=production_req['item_code']).first()
        
        production = Production(
            item_code=production_req['item_code'],
            description=production_req['description'],
            production_code=production_req['item_code'],  # Required field
            week_commencing=soh_record.week_commencing,
            calculation_factor=soh_record.calculation_factor or 1.0,
            requirement_kg=production_req['requirement_kg'],
            requirement_unit=production_req['requirement_unit']
        )
        
        db.session.add(production)
    
    @staticmethod
    def get_bom_explosion_summary(fg_code):
        """Get a complete BOM explosion summary for an FG item"""
        hierarchy = EnhancedBOMService.get_fg_hierarchy(fg_code)
        if not hierarchy:
            return None
        
        summary = {
            'fg_code': fg_code,
            'flow_type': hierarchy['flow_type'],
            'levels': []
        }
        
        # Level 1: FG → WIPF/WIP (if exists)
        if hierarchy['filling_code'] or hierarchy['production_code']:
            level1 = {
                'level': 1,
                'components': []
            }
            
            if hierarchy['filling_code']:
                level1['components'].append({
                    'type': 'WIPF',
                    'code': hierarchy['filling_code'],
                    'description': hierarchy['filling_description']
                })
            
            if hierarchy['production_code']:
                level1['components'].append({
                    'type': 'WIP', 
                    'code': hierarchy['production_code'],
                    'description': hierarchy['production_description']
                })
            
            summary['levels'].append(level1)
        
        # Level 2: WIPF/WIP → Raw Materials
        level2 = {
            'level': 2,
            'components': []
        }
        
        # Get raw materials for WIPF
        if hierarchy['filling_code']:
            filling_item = ItemMaster.query.filter_by(item_code=hierarchy['filling_code']).first()
            if filling_item:
                filling_recipes = RecipeMaster.query.filter_by(finished_good_id=filling_item.id).all()
                for recipe in filling_recipes:
                    rm_item = ItemMaster.query.get(recipe.raw_material_id)
                    level2['components'].append({
                        'type': 'RM',
                        'code': rm_item.item_code,
                        'description': rm_item.description,
                        'quantity': recipe.quantity,
                        'parent': hierarchy['filling_code']
                    })
        
        # Get raw materials for WIP
        if hierarchy['production_code']:
            production_item = ItemMaster.query.filter_by(item_code=hierarchy['production_code']).first()
            if production_item:
                production_recipes = RecipeMaster.query.filter_by(finished_good_id=production_item.id).all()
                for recipe in production_recipes:
                    rm_item = ItemMaster.query.get(recipe.raw_material_id)
                    level2['components'].append({
                        'type': 'RM',
                        'code': rm_item.item_code,
                        'description': rm_item.description,
                        'quantity': recipe.quantity,
                        'parent': hierarchy['production_code']
                    })
        
        if level2['components']:
            summary['levels'].append(level2)
        
        return summary 