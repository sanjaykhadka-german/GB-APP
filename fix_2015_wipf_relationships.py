from app import create_app, db
from models.item_master import ItemMaster

def fix_2015_wipf_relationships():
    """Fix the WIPF relationships for 2015 FG items"""
    print("Fixing 2015 WIPF relationships...\n")
    
    try:
        # Get the FG items
        fg_2015_100_2 = ItemMaster.query.filter_by(item_code='2015.100.2').first()
        fg_2015_125_02 = ItemMaster.query.filter_by(item_code='2015.125.02').first()
        
        # Get the WIPF items
        wipf_2015_100 = ItemMaster.query.filter_by(item_code='2015.100').first()
        wipf_2015_125 = ItemMaster.query.filter_by(item_code='2015.125').first()
        
        if not all([fg_2015_100_2, fg_2015_125_02, wipf_2015_100, wipf_2015_125]):
            print("❌ Not all required items found:")
            print(f"   FG 2015.100.2: {'✓' if fg_2015_100_2 else '✗'}")
            print(f"   FG 2015.125.02: {'✓' if fg_2015_125_02 else '✗'}")
            print(f"   WIPF 2015.100: {'✓' if wipf_2015_100 else '✗'}")
            print(f"   WIPF 2015.125: {'✓' if wipf_2015_125 else '✗'}")
            return
        
        print("Current relationships:")
        print(f"   FG 2015.100.2 → WIPF ID: {fg_2015_100_2.wipf_item_id} ({fg_2015_100_2.wipf_item.item_code if fg_2015_100_2.wipf_item else 'None'})")
        print(f"   FG 2015.125.02 → WIPF ID: {fg_2015_125_02.wipf_item_id} ({fg_2015_125_02.wipf_item.item_code if fg_2015_125_02.wipf_item else 'None'})")
        
        print("\nFixing relationships:")
        
        # Fix FG 2015.100.2 to point to WIPF 2015.100
        old_wipf_id = fg_2015_100_2.wipf_item_id
        fg_2015_100_2.wipf_item_id = wipf_2015_100.id
        print(f"   ✓ FG 2015.100.2: WIPF ID {old_wipf_id} → {wipf_2015_100.id} ({wipf_2015_100.item_code})")
        
        # Verify FG 2015.125.02 points to WIPF 2015.125 (should already be correct)
        if fg_2015_125_02.wipf_item_id != wipf_2015_125.id:
            old_wipf_id = fg_2015_125_02.wipf_item_id
            fg_2015_125_02.wipf_item_id = wipf_2015_125.id
            print(f"   ✓ FG 2015.125.02: WIPF ID {old_wipf_id} → {wipf_2015_125.id} ({wipf_2015_125.item_code})")
        else:
            print(f"   ✓ FG 2015.125.02: Already correctly linked to {wipf_2015_125.item_code}")
        
        # Commit changes
        db.session.commit()
        
        print("\nNew relationships:")
        db.session.refresh(fg_2015_100_2)
        db.session.refresh(fg_2015_125_02)
        print(f"   FG 2015.100.2 → WIPF ID: {fg_2015_100_2.wipf_item_id} ({fg_2015_100_2.wipf_item.item_code})")
        print(f"   FG 2015.125.02 → WIPF ID: {fg_2015_125_02.wipf_item_id} ({fg_2015_125_02.wipf_item.item_code})")
        
        print("\n✅ WIPF relationships fixed successfully!")
        print("\n⚠️  NOTE: You need to:")
        print("   1. Truncate the filling table (existing entries have wrong aggregation)")
        print("   2. Re-upload your SOH file to regenerate filling entries with correct relationships")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error fixing relationships: {str(e)}")
        raise

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        fix_2015_wipf_relationships() 