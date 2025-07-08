from app import create_app, db
from models.packing import Packing
from models.filling import Filling
from models.production import Production
from models.item_master import ItemMaster
from models.item_type import ItemType
from models.usage_report_table import UsageReportTable
from models.raw_material_report_table import RawMaterialReportTable
from datetime import datetime
import logging
from decimal import Decimal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_production_aggregation():
    """Fix production aggregation by properly grouping by WIP"""
    try:
        # Get all unique dates with packing entries
        packing_dates = db.session.query(
            Packing.packing_date,
            Packing.week_commencing
        ).distinct().all()
        
        for pack_date, week_comm in packing_dates:
            logger.info(f"\nProcessing date: {pack_date}, week: {week_comm}")
            
            # Group packing by WIP items
            wip_totals = {}
            packing_entries = Packing.query.filter_by(
                packing_date=pack_date,
                week_commencing=week_comm
            ).all()
            
            for packing in packing_entries:
                if not packing.item or not packing.item.wip_item:
                    continue
                    
                wip_item = packing.item.wip_item
                wip_code = wip_item.item_code
                
                if wip_code not in wip_totals:
                    wip_totals[wip_code] = {
                        'total_kg': 0.0,
                        'wip_item': wip_item
                    }
                
                wip_totals[wip_code]['total_kg'] += packing.requirement_kg or 0.0
            
            # Delete existing production entries
            Production.query.filter_by(
                production_date=pack_date,
                week_commencing=week_comm
            ).delete()
            
            # Create new aggregated production entries
            for wip_code, data in wip_totals.items():
                if data['total_kg'] <= 0:
                    continue
                    
                batches = data['total_kg'] / 300.0
                
                new_production = Production(
                    production_date=pack_date,
                    week_commencing=week_comm,
                    item_id=data['wip_item'].id,
                    production_code=wip_code,
                    description=data['wip_item'].description,
                    total_kg=data['total_kg'],
                    batches=batches
                )
                db.session.add(new_production)
            
            db.session.commit()
            logger.info(f"Fixed production aggregation for {pack_date}")
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error fixing production aggregation: {str(e)}")
        raise

def fix_filling_aggregation():
    """Fix filling aggregation by properly grouping by WIPF"""
    try:
        # Get all unique dates with packing entries
        packing_dates = db.session.query(
            Packing.packing_date,
            Packing.week_commencing
        ).distinct().all()
        
        for pack_date, week_comm in packing_dates:
            logger.info(f"\nProcessing date: {pack_date}, week: {week_comm}")
            
            # Group packing by WIPF items
            wipf_totals = {}
            packing_entries = Packing.query.filter_by(
                packing_date=pack_date,
                week_commencing=week_comm
            ).all()
            
            for packing in packing_entries:
                if not packing.item or not packing.item.wipf_item:
                    continue
                    
                wipf_item = packing.item.wipf_item
                wipf_code = wipf_item.item_code
                
                if wipf_code not in wipf_totals:
                    wipf_totals[wipf_code] = {
                        'total_kg': 0.0,
                        'total_units': 0,
                        'wipf_item': wipf_item
                    }
                
                wipf_totals[wipf_code]['total_kg'] += packing.requirement_kg or 0.0
                wipf_totals[wipf_code]['total_units'] += packing.requirement_unit or 0
            
            # Delete existing filling entries
            Filling.query.filter_by(
                filling_date=pack_date,
                week_commencing=week_comm
            ).delete()
            
            # Create new aggregated filling entries
            for wipf_code, data in wipf_totals.items():
                if data['total_kg'] <= 0:
                    continue
                    
                new_filling = Filling(
                    filling_date=pack_date,
                    week_commencing=week_comm,
                    item_id=data['wipf_item'].id,
                    requirement_kg=data['total_kg'],
                    kilo_per_size=data['total_kg']
                )
                db.session.add(new_filling)
            
            db.session.commit()
            logger.info(f"Fixed filling aggregation for {pack_date}")
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error fixing filling aggregation: {str(e)}")
        raise

def fix_missing_wipf():
    """Create missing WIPF items and link them to FG items"""
    try:
        # Get WIPF item type
        wipf_type = ItemType.query.filter_by(type_name='WIPF').first()
        if not wipf_type:
            raise Exception("WIPF item type not found")
            
        # Create missing WIPF items
        for code in ['2015.100', '2015.125']:
            existing_wipf = ItemMaster.query.filter_by(item_code=code).first()
            if not existing_wipf:
                new_wipf = ItemMaster(
                    item_code=code,
                    description=f"WIPF for {code}",
                    item_type_id=wipf_type.id
                )
                db.session.add(new_wipf)
                db.session.flush()
                logger.info(f"Created WIPF item {code}")
                
                # Link FG to WIPF
                fg_code = f"{code}.2" if '100' in code else f"{code}.02"
                fg_item = ItemMaster.query.filter_by(item_code=fg_code).first()
                if fg_item:
                    fg_item.wipf_item_id = new_wipf.id
                    logger.info(f"Linked FG {fg_code} to WIPF {code}")
        
        db.session.commit()
        logger.info("Fixed missing WIPF items")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error fixing missing WIPF: {str(e)}")
        raise

def fix_usage_reports():
    """Regenerate usage reports with correct recipe codes and values"""
    try:
        # Clear existing reports
        UsageReportTable.query.delete()
        RawMaterialReportTable.query.delete()
        
        # Get all production entries
        productions = Production.query.all()
        
        for prod in productions:
            if not prod.item:
                continue
                
            # Calculate recipe totals
            recipe_total = sum(Decimal(str(r.quantity_kg or 0)) for r in prod.item.components)
            if recipe_total <= 0:
                continue
                
            # Create usage reports for each component
            for recipe in prod.item.components:
                if not recipe.component_item:
                    continue
                    
                recipe_qty = Decimal(str(recipe.quantity_kg or 0))
                prod_total = Decimal(str(prod.total_kg or 0))
                
                usage_kg = float((recipe_qty / recipe_total) * prod_total)
                percentage = float((recipe_qty / recipe_total) * 100)
                
                # Create usage report
                usage_report = UsageReportTable(
                    week_commencing=prod.week_commencing,
                    production_date=prod.production_date,
                    recipe_code=prod.item.item_code,
                    raw_material=recipe.component_item.description,
                    usage_kg=usage_kg,
                    percentage=percentage
                )
                db.session.add(usage_report)
                
                # Create raw material report
                raw_report = RawMaterialReportTable(
                    week_commencing=prod.week_commencing,
                    production_date=prod.production_date,
                    raw_material_id=recipe.component_item.id,
                    raw_material=recipe.component_item.description,
                    meat_required=usage_kg
                )
                db.session.add(raw_report)
        
        db.session.commit()
        logger.info("Fixed usage reports")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error fixing usage reports: {str(e)}")
        raise

def fix_all_issues():
    """Fix all aggregation and reporting issues"""
    try:
        # 1. Fix missing WIPF items first
        fix_missing_wipf()
        
        # 2. Fix production aggregation
        fix_production_aggregation()
        
        # 3. Fix filling aggregation
        fix_filling_aggregation()
        
        # 4. Regenerate usage reports
        fix_usage_reports()
        
        logger.info("Successfully fixed all issues")
        
    except Exception as e:
        logger.error(f"Error during fix: {str(e)}")
        raise

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        fix_all_issues() 