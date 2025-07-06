from app import app
from models.item_master import ItemMaster
from models.item_type import ItemType
#from models.joining import Joining
from database import db
import sqlalchemy as sa

with app.app_context():
    # Count items by type
    types = db.session.query(ItemType.type_name, sa.func.count(ItemMaster.id)).join(ItemMaster, ItemType.id == ItemMaster.item_type_id).group_by(ItemType.type_name).all()
    print('Item counts by type:')
    for type_name, count in types:
        print(f'  {type_name}: {count}')

    # Check if joining table has data
    joining_count = Joining.query.count()
    print(f'\nJoining table records: {joining_count}')

    if joining_count > 0:
        sample = Joining.query.limit(5).all()
        print('\nSample joining records:')
        for j in sample:
            print(f'  FG: {j.fg_code} → WIPF: {j.filling_code} → WIP: {j.production_code}')
    
    # Check manufacturing flow patterns
    print('\nManufacturing flows in joining table:')
    flows = db.session.query(
        sa.func.count(Joining.id).label('count'),
        sa.case(
            (sa.and_(Joining.filling_code.isnot(None), Joining.production_code.isnot(None)), 'Complex (FG→WIPF→WIP)'),
            (Joining.filling_code.isnot(None), 'Filling (FG→WIPF)'),
            (Joining.production_code.isnot(None), 'Production (FG→WIP)'),
            else_='Direct (FG only)'
        ).label('flow_type')
    ).group_by('flow_type').all()
    
    for count, flow_type in flows:
        print(f'  {flow_type}: {count} records') 