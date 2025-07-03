from app import app
from models.item_master import ItemMaster
from models.joining import Joining
from database import db
import sqlalchemy as sa

def migrate_hierarchy_data():
    """Migrate hierarchy data from joining table to item_master fields"""
    
    with app.app_context():
        print("🔄 Migrating hierarchy data from joining table to item_master...")
        
        # Get all joining records
        joining_records = Joining.query.all()
        print(f"Found {len(joining_records)} joining records to migrate")
        
        updated_count = 0
        error_count = 0
        
        for joining in joining_records:
            try:
                # Find the FG item in item_master
                fg_item = ItemMaster.query.filter_by(item_code=joining.fg_code).first()
                
                if not fg_item:
                    print(f"❌ FG item not found: {joining.fg_code}")
                    error_count += 1
                    continue
                
                # Find WIP item if specified
                wip_item = None
                if joining.production_code:
                    wip_item = ItemMaster.query.filter_by(item_code=joining.production_code).first()
                    if not wip_item:
                        print(f"⚠️  WIP item not found: {joining.production_code} for FG {joining.fg_code}")
                
                # Find WIPF item if specified  
                wipf_item = None
                if joining.filling_code:
                    wipf_item = ItemMaster.query.filter_by(item_code=joining.filling_code).first()
                    if not wipf_item:
                        print(f"⚠️  WIPF item not found: {joining.filling_code} for FG {joining.fg_code}")
                
                # Update the FG item with hierarchy information
                fg_item.wip_item_id = wip_item.id if wip_item else None
                fg_item.wipf_item_id = wipf_item.id if wipf_item else None
                
                updated_count += 1
                print(f"✅ Updated {joining.fg_code}: WIP={joining.production_code}, WIPF={joining.filling_code}")
                
            except Exception as e:
                print(f"❌ Error processing {joining.fg_code}: {str(e)}")
                error_count += 1
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\n🎉 Migration completed!")
            print(f"✅ Successfully updated: {updated_count} FG items")
            print(f"❌ Errors: {error_count}")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Failed to commit changes: {str(e)}")
            return False
        
        return True

def verify_migration():
    """Verify the migration was successful"""
    
    with app.app_context():
        print("\n🔍 Verifying migration...")
        
        # Count FG items with hierarchy data
        fg_items = db.session.query(ItemMaster).join(
            ItemMaster.item_type
        ).filter(
            ItemMaster.item_type.has(type_name='FG')
        ).all()
        
        wip_populated = len([fg for fg in fg_items if fg.wip_item_id is not None])
        wipf_populated = len([fg for fg in fg_items if fg.wipf_item_id is not None])
        
        print(f"📊 Results after migration:")
        print(f"   Total FG items: {len(fg_items)}")
        print(f"   FG with wip_item_id: {wip_populated}")
        print(f"   FG with wipf_item_id: {wipf_populated}")
        
        # Show sample results
        print(f"\n📋 Sample hierarchy (item_master):")
        for fg in fg_items[:5]:
            wip_code = fg.wip_component.item_code if fg.wip_component else "None"
            wipf_code = fg.wipf_component.item_code if fg.wipf_component else "None"
            print(f"   FG: {fg.item_code} → WIP: {wip_code} → WIPF: {wipf_code}")

if __name__ == "__main__":
    print("🚀 Starting hierarchy data migration...")
    print("This will move data from joining table to item_master fields")
    
    if migrate_hierarchy_data():
        verify_migration()
        print("\n✅ Migration completed successfully!")
        print("\n💡 Next steps:")
        print("   1. Verify the data looks correct")
        print("   2. Update any code that uses joining table to use item_master instead")
        print("   3. Consider dropping the joining table once everything is verified")
    else:
        print("\n❌ Migration failed!") 