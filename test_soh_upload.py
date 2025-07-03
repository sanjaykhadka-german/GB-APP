#!/usr/bin/env python3
"""
Test SOH Upload Process
=======================

Test SOH upload to see if it creates filling and production entries correctly.
"""

from app import app
from controllers.soh_controller import create_packing_entry_from_soh
from models.item_master import ItemMaster
from models.item_type import ItemType
from models.packing import Packing
from models.filling import Filling
from models.production import Production
from database import db
from datetime import datetime, date

def test_soh_upload():
    """Test SOH upload process"""
    
    with app.app_context():
        print("🔍 Testing SOH Upload Process...")
        print("=" * 50)
        
        # Get a sample FG item to test
        fg_item = db.session.query(ItemMaster).join(ItemType).filter(
            ItemType.type_name == 'FG',
            ItemMaster.wip_item_id.isnot(None)  # Has WIP relationship
        ).first()
        
        if not fg_item:
            print("❌ No FG items with WIP relationships found")
            return
            
        print(f"📋 Testing with FG: {fg_item.item_code} - {fg_item.description}")
        print(f"   WIP relationship: {fg_item.wip_item_id} -> {fg_item.wip_component.item_code if fg_item.wip_component else 'None'}")
        
        # Test week
        test_week = date.today()
        
        # Clean up any existing test data
        print("🧹 Cleaning up existing test data...")
        Packing.query.filter_by(item_id=fg_item.id, week_commencing=test_week).delete()
        if fg_item.wip_component:
            Filling.query.filter_by(item_id=fg_item.wip_component.id, week_commencing=test_week).delete()
            Production.query.filter_by(item_id=fg_item.wip_component.id, week_commencing=test_week).delete()
        db.session.commit()
        
        # Test SOH upload
        print(f"\n🔄 Testing SOH upload for {fg_item.item_code}...")
        
        # Simulate SOH data
        soh_total_units = 50  # Below min level to trigger requirements
        
        try:
            success, message = create_packing_entry_from_soh(
                fg_code=fg_item.item_code,
                description=fg_item.description,
                week_commencing=test_week,
                soh_total_units=soh_total_units,
                item=fg_item
            )
            
            print(f"SOH Upload Result: {'✅ Success' if success else '❌ Failed'}")
            print(f"Message: {message}")
            
            # Check what was created
            print("\n📊 Checking created entries...")
            
            packing_count = Packing.query.filter_by(item_id=fg_item.id, week_commencing=test_week).count()
            print(f"   Packing entries: {packing_count}")
            
            if fg_item.wip_component:
                filling_count = Filling.query.filter_by(item_code=fg_item.wip_component.item_code, week_commencing=test_week).count()
                production_count = Production.query.filter_by(item_code=fg_item.wip_component.item_code, week_commencing=test_week).count()
                print(f"   Filling entries: {filling_count}")
                print(f"   Production entries: {production_count}")
            
            if packing_count > 0:
                packing = Packing.query.filter_by(item_id=fg_item.id, week_commencing=test_week).first()
                print(f"   Packing requirement_kg: {packing.requirement_kg}")
                print(f"   Packing requirement_unit: {packing.requirement_unit}")
                
        except Exception as e:
            print(f"❌ Error during SOH upload: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_soh_upload() 