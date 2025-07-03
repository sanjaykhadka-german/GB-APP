#!/usr/bin/env python3
"""
DATABASE SCHEMA MIGRATION SCRIPT
Migrates to simplified two-table design
"""

import os
from sqlalchemy import text
from database import db
from app import create_app

def main():
    """Main migration function"""
    print("🚀 STARTING DATABASE SCHEMA MIGRATION")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Step 1: Backup
            print("📁 Creating backups...")
            db.session.execute(text("CREATE TABLE item_master_backup AS SELECT * FROM item_master"))
            db.session.execute(text("CREATE TABLE recipe_master_backup AS SELECT * FROM recipe_master"))
            
            # Step 2: Add new columns
            print("🏗️  Adding new columns...")
            db.session.execute(text("ALTER TABLE item_master ADD COLUMN item_type VARCHAR(20)"))
            db.session.execute(text("ALTER TABLE item_master ADD COLUMN wip_item_id INT NULL"))
            db.session.execute(text("ALTER TABLE item_master ADD COLUMN wipf_item_id INT NULL"))
            
            # Step 3: Populate item_type
            print("📋 Populating item_type...")
            db.session.execute(text("""
                UPDATE item_master im 
                JOIN item_type it ON im.item_type_id = it.id 
                SET im.item_type = it.type_name
            """))
            
            # Step 4: Create recipe_components table
            print("🍳 Creating recipe_components table...")
            db.session.execute(text("""
                CREATE TABLE recipe_components (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    wip_item_id INT NOT NULL,
                    rm_item_id INT NOT NULL,
                    quantity_kg DECIMAL(10,3) NOT NULL,
                    recipe_code VARCHAR(50),
                    step_order INT DEFAULT 1,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (wip_item_id) REFERENCES item_master(id) ON DELETE CASCADE,
                    FOREIGN KEY (rm_item_id) REFERENCES item_master(id) ON DELETE CASCADE,
                    CHECK (quantity_kg > 0),
                    UNIQUE(wip_item_id, rm_item_id)
                )
            """))
            
            # Step 5: Migrate recipe data
            print("🔄 Migrating recipes...")
            db.session.execute(text("""
                INSERT INTO recipe_components (wip_item_id, rm_item_id, quantity_kg, recipe_code, created_at)
                SELECT 
                    rm.finished_good_id,
                    rm.raw_material_id,
                    rm.kg_per_batch,
                    rm.recipe_code,
                    rm.created_at
                FROM recipe_master rm
                JOIN item_master im ON rm.finished_good_id = im.id
                WHERE im.item_type = 'WIP'
            """))
            
            # Step 6: Add constraints
            print("🔗 Adding constraints...")
            db.session.execute(text("ALTER TABLE item_master ADD CONSTRAINT fk_wip FOREIGN KEY (wip_item_id) REFERENCES item_master(id)"))
            db.session.execute(text("ALTER TABLE item_master ADD CONSTRAINT fk_wipf FOREIGN KEY (wipf_item_id) REFERENCES item_master(id)"))
            
            # Step 7: Create indexes
            print("📇 Creating indexes...")
            db.session.execute(text("CREATE INDEX idx_item_type ON item_master(item_type)"))
            db.session.execute(text("CREATE INDEX idx_wip_ref ON item_master(wip_item_id)"))
            db.session.execute(text("CREATE INDEX idx_recipe_wip ON recipe_components(wip_item_id)"))
            
            db.session.commit()
            print("🎉 MIGRATION COMPLETED!")
            
        except Exception as e:
            print(f"❌ MIGRATION FAILED: {e}")
            db.session.rollback()
            return False
    
    return True

if __name__ == "__main__":
    main() 