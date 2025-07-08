from app import create_app, db
from models.item_master import ItemMaster
from sqlalchemy import text

def verify_item_master_wipf():
    """Show the exact item_master table data for WIPF relationships"""
    print("Checking item_master table WIPF relationships...\n")
    
    # Check FG items and their WIPF relationships
    print("=== FG Items and their WIPF relationships ===")
    query = """
    SELECT 
        fg.id as fg_id,
        fg.item_code as fg_code,
        fg.description as fg_description,
        fg.wipf_item_id,
        wipf.item_code as wipf_code,
        wipf.description as wipf_description
    FROM item_master fg
    LEFT JOIN item_master wipf ON fg.wipf_item_id = wipf.id
    WHERE fg.item_code IN ('2015.100.2', '2015.125.02')
    ORDER BY fg.item_code
    """
    
    results = db.session.execute(text(query)).fetchall()
    
    for result in results:
        print(f"FG {result.fg_code} (ID: {result.fg_id})")
        print(f"   Description: {result.fg_description}")
        print(f"   wipf_item_id: {result.wipf_item_id}")
        print(f"   Links to WIPF: {result.wipf_code} ({result.wipf_description})")
        print()
    
    print("=== WIPF Items ===")
    wipf_query = """
    SELECT 
        id,
        item_code,
        description,
        item_type_id
    FROM item_master
    WHERE item_code IN ('2015.100', '2015.125')
    ORDER BY item_code
    """
    
    wipf_results = db.session.execute(text(wipf_query)).fetchall()
    
    for result in wipf_results:
        print(f"WIPF {result.item_code} (ID: {result.id})")
        print(f"   Description: {result.description}")
        print(f"   Item Type ID: {result.item_type_id}")
        print()
    
    print("=== What the relationships SHOULD be ===")
    print("FG 2015.100.2 should link to WIPF 2015.100")
    print("FG 2015.125.02 should link to WIPF 2015.125")
    
    # Check if the fix was applied
    print("\n=== Current Status After Fix ===")
    fg_2015_100_2 = ItemMaster.query.filter_by(item_code='2015.100.2').first()
    fg_2015_125_02 = ItemMaster.query.filter_by(item_code='2015.125.02').first()
    
    if fg_2015_100_2:
        wipf_item = ItemMaster.query.get(fg_2015_100_2.wipf_item_id) if fg_2015_100_2.wipf_item_id else None
        status = "✅ CORRECT" if wipf_item and wipf_item.item_code == '2015.100' else "❌ INCORRECT"
        print(f"FG 2015.100.2 → WIPF {wipf_item.item_code if wipf_item else 'None'} {status}")
    
    if fg_2015_125_02:
        wipf_item = ItemMaster.query.get(fg_2015_125_02.wipf_item_id) if fg_2015_125_02.wipf_item_id else None
        status = "✅ CORRECT" if wipf_item and wipf_item.item_code == '2015.125' else "❌ INCORRECT"
        print(f"FG 2015.125.02 → WIPF {wipf_item.item_code if wipf_item else 'None'} {status}")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        verify_item_master_wipf() 