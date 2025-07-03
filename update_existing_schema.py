#!/usr/bin/env python3
"""
Update existing schema with new columns for simplified design
"""

from sqlalchemy import text
from database import db
from app import create_app

def main():
    """Main migration function"""
    print("🚀 UPDATING EXISTING SCHEMA")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Step 1: Backup
            print("📁 Creating backups...")
            db.session.execute(text("CREATE TABLE IF NOT EXISTS item_master_backup AS SELECT * FROM item_master"))
            
            # Step 2: Add new columns to item_master
            print("🏗️  Adding new columns...")
            
            # Add item_type column (direct string)
            try:
                db.session.execute(text("ALTER TABLE item_master ADD COLUMN item_type VARCHAR(20) NULL"))
                print("  ✅ Added item_type column")
            except:
                print("  ⚠️  item_type column may already exist")
            
            # Add self-referencing FKs for FG composition
            try:
                db.session.execute(text("ALTER TABLE item_master ADD COLUMN wip_item_id INT NULL"))
                print("  ✅ Added wip_item_id column")
            except:
                print("  ⚠️  wip_item_id column may already exist")
            
            try:
                db.session.execute(text("ALTER TABLE item_master ADD COLUMN wipf_item_id INT NULL"))
                print("  ✅ Added wipf_item_id column")
            except:
                print("  ⚠️  wipf_item_id column may already exist")
            
            # Step 3: Populate item_type from existing lookup
            print("📋 Populating item_type...")
            db.session.execute(text("""
                UPDATE item_master im 
                JOIN item_type it ON im.item_type_id = it.id 
                SET im.item_type = it.type_name
                WHERE im.item_type IS NULL
            """))
            
            # Step 4: Add foreign key constraints
            print("🔗 Adding constraints...")
            try:
                db.session.execute(text("ALTER TABLE item_master ADD CONSTRAINT fk_wip_item FOREIGN KEY (wip_item_id) REFERENCES item_master(id)"))
                print("  ✅ Added wip_item FK constraint")
            except:
                print("  ⚠️  wip_item FK may already exist")
            
            try:
                db.session.execute(text("ALTER TABLE item_master ADD CONSTRAINT fk_wipf_item FOREIGN KEY (wipf_item_id) REFERENCES item_master(id)"))
                print("  ✅ Added wipf_item FK constraint")
            except:
                print("  ⚠️  wipf_item FK may already exist")
            
            # Step 5: Create indexes
            print("📇 Creating indexes...")
            try:
                db.session.execute(text("CREATE INDEX idx_item_type_direct ON item_master(item_type)"))
                print("  ✅ Added item_type index")
            except:
                print("  ⚠️  item_type index may already exist")
            
            try:
                db.session.execute(text("CREATE INDEX idx_wip_item_ref ON item_master(wip_item_id)"))
                print("  ✅ Added wip_item index")
            except:
                print("  ⚠️  wip_item index may already exist")
            
            db.session.commit()
            
            # Step 6: Validation
            print("✅ Validating migration...")
            result = db.session.execute(text("SELECT item_type, COUNT(*) FROM item_master GROUP BY item_type"))
            for row in result:
                print(f"  📊 {row[0] or 'NULL'}: {row[1]} items")
            
            print("🎉 MIGRATION COMPLETED!")
            
        except Exception as e:
            print(f"❌ MIGRATION FAILED: {e}")
            db.session.rollback()
            return False
    
    return True

if __name__ == "__main__":
    main() 