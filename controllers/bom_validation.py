"""
BOM Service Validation Module
This module provides proper validation functions to prevent aggregation issues
instead of hardcoded fixes after the fact.
"""

from flask import jsonify
from database import db
from models import ItemMaster, Recipe, RecipeDetail, Production, ProductionDetail, Packing, PackingDetail, SOH, Filling
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta

class BOMValidator:
    """
    Proper validation class to detect and prevent BOM aggregation issues
    """
    
    def validate_wip_aggregation(self):
        """
        Validate that items with same WIP code are properly aggregated
        Returns list of issues found
        """
        issues = []
        
        # Check production table aggregation
        production_wips = db.session.query(
            Production.wip_code,
            func.count(Production.id).label('count'),
            func.sum(Production.quantity).label('total_qty')
        ).group_by(Production.wip_code).having(func.count(Production.id) > 1).all()
        
        for wip_result in production_wips:
            wip_code = wip_result.wip_code
            count = wip_result.count
            
            # Get all items that should be aggregated under this WIP
            items = db.session.query(Production).filter_by(wip_code=wip_code).all()
            
            issues.append({
                'type': 'WIP_NOT_AGGREGATED',
                'wip_code': wip_code,
                'count': count,
                'items': [{'id': item.id, 'fg_code': item.fg_code, 'quantity': item.quantity} for item in items],
                'description': f"WIP {wip_code} has {count} separate entries instead of being aggregated"
            })
        
        return issues
    
    def validate_wipf_aggregation(self):
        """
        Validate that items with same WIPF code are properly aggregated
        Returns list of issues found
        """
        issues = []
        
        # Check filling table aggregation
        filling_wipfs = db.session.query(
            Filling.wipf_code,
            Filling.week_commencing,
            func.count(Filling.id).label('count'),
            func.sum(Filling.requirement).label('total_req')
        ).group_by(
            Filling.wipf_code, 
            Filling.week_commencing
        ).having(func.count(Filling.id) > 1).all()
        
        for wipf_result in filling_wipfs:
            wipf_code = wipf_result.wipf_code
            week = wipf_result.week_commencing
            count = wipf_result.count
            
            # Get all items that should be aggregated under this WIPF
            items = db.session.query(Filling).filter_by(
                wipf_code=wipf_code,
                week_commencing=week
            ).all()
            
            issues.append({
                'type': 'WIPF_NOT_AGGREGATED',
                'wipf_code': wipf_code,
                'week_commencing': week,
                'count': count,
                'items': [{'id': item.id, 'requirement': item.requirement} for item in items],
                'description': f"WIPF {wipf_code} for week {week} has {count} separate entries instead of being aggregated"
            })
        
        return issues
    
    def validate_total_consistency(self):
        """
        Validate that production and packing totals are consistent
        Returns list of issues found
        """
        issues = []
        
        # Get production total
        production_total = db.session.query(func.sum(Production.quantity)).scalar() or 0
        
        # Get packing total  
        packing_total = db.session.query(func.sum(Packing.quantity)).scalar() or 0
        
        if abs(production_total - packing_total) > 0.01:  # Allow for small rounding differences
            issues.append({
                'type': 'TOTAL_MISMATCH',
                'production_total': production_total,
                'packing_total': packing_total,
                'difference': abs(production_total - packing_total),
                'description': f"Production total ({production_total:.2f}) doesn't match packing total ({packing_total:.2f})"
            })
        
        return issues
    
    def validate_wipf_relationships(self):
        """
        Validate that FG items have correct WIPF relationships
        Returns list of issues found
        """
        issues = []
        
        # Get all SOH entries with requirements > 0
        soh_entries = SOH.query.filter(SOH.requirement > 0).all()
        
        for soh_entry in soh_entries:
            fg_item = ItemMaster.query.filter_by(item_code=soh_entry.fg_code).first()
            
            if fg_item and fg_item.wipf_item_id:
                # Extract expected WIPF base from FG code
                fg_parts = fg_item.item_code.split('.')
                if len(fg_parts) >= 2:
                    expected_wipf_base = f"{fg_parts[0]}.{fg_parts[1]}"
                    
                    # Check actual WIPF relationship
                    if fg_item.wipf_item and not fg_item.wipf_item.item_code.startswith(expected_wipf_base):
                        issues.append({
                            'type': 'INCORRECT_WIPF_RELATIONSHIP',
                            'fg_code': fg_item.item_code,
                            'expected_wipf_base': expected_wipf_base,
                            'actual_wipf': fg_item.wipf_item.item_code,
                            'description': f"FG {fg_item.item_code} should link to WIPF {expected_wipf_base}* but links to {fg_item.wipf_item.item_code}"
                        })
            elif fg_item and not fg_item.wipf_item_id:
                # FG item has no WIPF relationship but should have one
                issues.append({
                    'type': 'MISSING_WIPF_RELATIONSHIP',
                    'fg_code': fg_item.item_code,
                    'description': f"FG {fg_item.item_code} has SOH requirement but no WIPF relationship"
                })
        
        return issues
    
    def run_full_validation(self):
        """
        Run all validation checks and return comprehensive report
        """
        print("Running BOM Service Validation...\n")
        
        all_issues = []
        
        # Run all validation checks
        wip_issues = self.validate_wip_aggregation()
        wipf_issues = self.validate_wipf_aggregation()
        total_issues = self.validate_total_consistency()
        relationship_issues = self.validate_wipf_relationships()
        
        all_issues.extend(wip_issues)
        all_issues.extend(wipf_issues)
        all_issues.extend(total_issues)
        all_issues.extend(relationship_issues)
        
        # Report results
        if all_issues:
            print(f"⚠️  Found {len(all_issues)} BOM validation issues:\n")
            
            for issue in all_issues:
                print(f"Issue Type: {issue['type']}")
                print(f"Description: {issue['description']}")
                
                if issue['type'] == 'WIP_NOT_AGGREGATED':
                    print(f"  WIP Code: {issue['wip_code']}")
                    print(f"  Entries: {issue['count']}")
                    for item in issue['items']:
                        print(f"    - FG {item['fg_code']}: {item['quantity']} kg")
                
                elif issue['type'] == 'WIPF_NOT_AGGREGATED':
                    print(f"  WIPF Code: {issue['wipf_code']}")
                    print(f"  Week: {issue['week_commencing']}")
                    print(f"  Entries: {issue['count']}")
                    for item in issue['items']:
                        print(f"    - Requirement: {item['requirement']} kg")
                
                elif issue['type'] == 'TOTAL_MISMATCH':
                    print(f"  Production Total: {issue['production_total']:.2f} kg")
                    print(f"  Packing Total: {issue['packing_total']:.2f} kg")
                    print(f"  Difference: {issue['difference']:.2f} kg")
                
                print()
            
            return all_issues
        else:
            print("✅ All BOM validations passed!")
            return []

def validate_before_soh_upload():
    """
    Function to run before SOH upload to catch issues early
    """
    validator = BOMValidator()
    relationship_issues = validator.validate_wipf_relationships()
    
    if relationship_issues:
        print("❌ WIPF relationship issues detected! Please fix before uploading SOH:")
        for issue in relationship_issues:
            print(f"  - {issue['description']}")
        return False
    else:
        print("✅ WIPF relationships validated successfully!")
        return True

def validate_after_bom_generation():
    """
    Function to run after BOM generation to verify results
    """
    validator = BOMValidator()
    issues = validator.run_full_validation()
    
    if issues:
        print("\n⚠️  BOM generation completed with issues. Consider re-running with fixes.")
        return False
    else:
        print("\n✅ BOM generation completed successfully with no issues!")
        return True 