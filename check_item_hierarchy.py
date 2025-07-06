from app import app
from models.item_master import ItemMaster
from models.item_type import ItemType
from models.joining import Joining
from database import db
import sqlalchemy as sa

with app.app_context():
    print("=== ITEM MASTER HIERARCHY ===")
    
    # Check FG items with their WIP/WIPF relationships
    fg_items = db.session.query(ItemMaster).join(ItemType).filter(
        ItemType.type_name == 'FG'
    ).all()
    
    print(f"Total FG items: {len(fg_items)}")
    
    fg_with_wip = [fg for fg in fg_items if fg.wip_item_id is not None]
    fg_with_wipf = [fg for fg in fg_items if fg.wipf_item_id is not None]
    
    print(f"FG items with wip_item_id: {len(fg_with_wip)}")
    print(f"FG items with wipf_item_id: {len(fg_with_wipf)}")
    
    print("\nSample FG hierarchy from item_master:")
    for fg in fg_items[:5]:
        wip_code = fg.wip_item.item_code if fg.wip_item else "None"
        wipf_code = fg.wipf_item.item_code if fg.wipf_item else "None"
        print(f"  FG: {fg.item_code} → WIP: {wip_code} → WIPF: {wipf_code}")
    
    print("\n=== JOINING TABLE HIERARCHY ===")
    
    joining_records = Joining.query.limit(5).all()
    print("Sample joining table records:")
    for j in joining_records:
        print(f"  FG: {j.fg_code} → WIPF: {j.filling_code} → WIP: {j.production_code}")
    
    print("\n=== COMPARISON ===")
    
    # Check if data matches between tables
    matching_records = 0
    total_fg_checked = 0
    
    for fg in fg_items[:10]:  # Check first 10 for comparison
        total_fg_checked += 1
        joining_record = Joining.query.filter_by(fg_code=fg.item_code).first()
        
        if joining_record:
            item_wip = fg.wip_item.item_code if fg.wip_item else None
            item_wipf = fg.wipf_item.item_code if fg.wipf_item else None
            
            joining_wip = joining_record.production_code
            joining_wipf = joining_record.filling_code
            
            if item_wip == joining_wip and item_wipf == joining_wipf:
                matching_records += 1
                print(f"✅ MATCH: {fg.item_code}")
            else:
                print(f"❌ MISMATCH: {fg.item_code}")
                print(f"    ItemMaster: WIP={item_wip}, WIPF={item_wipf}")
                print(f"    Joining:    WIP={joining_wip}, WIPF={joining_wipf}")
    
    print(f"\nMatching records: {matching_records}/{total_fg_checked}") 