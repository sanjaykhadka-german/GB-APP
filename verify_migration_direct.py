from app import app
from models.item_master import ItemMaster
from models.item_type import ItemType
from database import db

with app.app_context():
    print("🔍 Checking migration results directly from database...")
    
    # Get sample FG items and check their wip_item_id and wipf_item_id values
    fg_items = db.session.query(ItemMaster).join(ItemType).filter(
        ItemType.type_name == 'FG'
    ).limit(10).all()
    
    print("📋 FG items with hierarchy data:")
    print("=" * 80)
    
    for fg in fg_items:
        wip_id = fg.wip_item_id
        wipf_id = fg.wipf_item_id
        
        # Get the actual item codes
        wip_code = "None"
        wipf_code = "None"
        
        if wip_id:
            wip_item = ItemMaster.query.get(wip_id)
            wip_code = wip_item.item_code if wip_item else f"ID:{wip_id}(NOT_FOUND)"
            
        if wipf_id:
            wipf_item = ItemMaster.query.get(wipf_id)
            wipf_code = wipf_item.item_code if wipf_item else f"ID:{wipf_id}(NOT_FOUND)"
        
        print(f"FG: {fg.item_code:15} → WIP: {wip_code:15} (ID:{wip_id}) → WIPF: {wipf_code:15} (ID:{wipf_id})")
    
    # Count statistics
    total_fg = db.session.query(ItemMaster).join(ItemType).filter(ItemType.type_name == 'FG').count()
    fg_with_wip = db.session.query(ItemMaster).join(ItemType).filter(
        ItemType.type_name == 'FG',
        ItemMaster.wip_item_id.isnot(None)
    ).count()
    fg_with_wipf = db.session.query(ItemMaster).join(ItemType).filter(
        ItemType.type_name == 'FG',
        ItemMaster.wipf_item_id.isnot(None)
    ).count()
    
    print("\n📊 Migration Statistics:")
    print(f"   Total FG items: {total_fg}")
    print(f"   FG with WIP mappings: {fg_with_wip}")
    print(f"   FG with WIPF mappings: {fg_with_wipf}")
    
    print(f"\n✅ Migration Success Rate:")
    print(f"   WIP mappings: {fg_with_wip}/{total_fg} ({100*fg_with_wip/total_fg:.1f}%)")
    print(f"   WIPF mappings: {fg_with_wipf}/{total_fg} ({100*fg_with_wipf/total_fg:.1f}%)") 