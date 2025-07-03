#!/usr/bin/env python3
"""
Database Migration: Transform to Flexible Component Schema
==========================================================

This script migrates to the updated schema where recipe components can be
RM (Raw Materials) OR WIP (Work-in-Progress) items, providing more flexibility.

Key Changes:
- recipe_master.component_rm_id → recipe_master.component_item_id
- Components can now be RM, WIP, or other item types
- More flexible multi-level BOM support

Schema Changes:
1. item_master: Simplified to exact user specification
2. recipe_master: Uses component_item_id for flexible component types
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add the parent directory to sys.path to import models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from database import db
from sqlalchemy import text

def create_app():
    """Create Flask app for migration"""
    
    # Load environment variables from .env file
    load_dotenv()
    
    app = Flask(__name__)
    
    # Use the same database configuration as the main app
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Validate database URL
    if not app.config['SQLALCHEMY_DATABASE_URI']:
        print("❌ SQLALCHEMY_DATABASE_URI is not set!")
        print("Please create a .env file with your database configuration:")
        print("SQLALCHEMY_DATABASE_URI=mysql+pymysql://username:password@localhost/gb_db")
        sys.exit(1)
    
    print(f"Using database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    db.init_app(app)
    return app

def backup_tables(app):
    """Create backup tables before migration"""
    print("Creating backup tables...")
    
    with app.app_context():
        try:
            # Backup item_master
            db.session.execute(text("""
                CREATE TABLE item_master_backup_flexible_schema 
                AS SELECT * FROM item_master
            """))
            
            # Backup recipe_master  
            db.session.execute(text("""
                CREATE TABLE recipe_master_backup_flexible_schema 
                AS SELECT * FROM recipe_master
            """))
            
            db.session.commit()
            print("✓ Backup tables created successfully")
            
        except Exception as e:
            print(f"✗ Error creating backups: {e}")
            db.session.rollback()
            raise

def migrate_item_master_schema(app):
    """Transform item_master to exact user specification"""
    print("Migrating item_master table schema...")
    
    with app.app_context():
        try:
            # Step 1: Convert foreign key lookups to string values
            print("  - Converting foreign key lookups to string values...")
            
            # Convert category_id to category string (if exists)
            try:
                db.session.execute(text("""
                    UPDATE item_master im
                    LEFT JOIN category c ON im.category_id = c.id
                    SET im.category = c.category_name
                    WHERE im.category_id IS NOT NULL
                """))
            except:
                print("    Category conversion skipped (no category table)")
            
            # Convert department_id to department string (if exists)
            try:
                db.session.execute(text("""
                    UPDATE item_master im
                    LEFT JOIN department d ON im.department_id = d.department_id
                    SET im.department = d.department_name
                    WHERE im.department_id IS NOT NULL
                """))
            except:
                print("    Department conversion skipped (no department table)")
            
            # Convert machinery_id to machinery string (if exists)
            try:
                db.session.execute(text("""
                    UPDATE item_master im
                    LEFT JOIN machinery m ON im.machinery_id = m.machineID
                    SET im.machinery = m.machine_name
                    WHERE im.machinery_id IS NOT NULL
                """))
            except:
                print("    Machinery conversion skipped (no machinery table)")
            
            # Step 2: Ensure required columns exist with correct types
            print("  - Updating column specifications...")
            
            # Add missing columns if they don't exist
            columns_to_add = [
                ("category", "VARCHAR(100)"),
                ("department", "VARCHAR(100)"),
                ("machinery", "VARCHAR(100)"),
                ("min_stock", "DECIMAL(10,2) DEFAULT 0.00"),
                ("max_stock", "DECIMAL(10,2) DEFAULT 0.00"),
                ("price_per_kg", "DECIMAL(12,4)"),
                ("is_make_to_order", "BOOLEAN DEFAULT FALSE"),
                ("loss_percentage", "DECIMAL(5,2) DEFAULT 0.00"),
                ("calculation_factor", "DECIMAL(10,4) DEFAULT 1.0000"),
                ("wip_item_id", "INT NULL"),
                ("wipf_item_id", "INT NULL")
            ]
            
            for column, definition in columns_to_add:
                try:
                    db.session.execute(text(f"ALTER TABLE item_master ADD COLUMN {column} {definition}"))
                    print(f"    Added {column}")
                except:
                    print(f"    {column} already exists")
            
            # Step 3: Modify existing columns to match specification
            try:
                db.session.execute(text("""
                    ALTER TABLE item_master 
                    MODIFY COLUMN item_code VARCHAR(50) NOT NULL,
                    MODIFY COLUMN description VARCHAR(255) NOT NULL
                """))
            except Exception as e:
                print(f"    Column modification warning: {e}")
            
            # Step 4: Add foreign key constraints for self-referencing relationships
            try:
                db.session.execute(text("""
                    ALTER TABLE item_master 
                    ADD CONSTRAINT fk_wip_item FOREIGN KEY (wip_item_id) REFERENCES item_master(id)
                """))
            except:
                print("    wip_item_id FK already exists")
            
            try:
                db.session.execute(text("""
                    ALTER TABLE item_master 
                    ADD CONSTRAINT fk_wipf_item FOREIGN KEY (wipf_item_id) REFERENCES item_master(id)
                """))
            except:
                print("    wipf_item_id FK already exists")
            
            # Step 5: Add index on item_code
            try:
                db.session.execute(text("""
                    CREATE INDEX idx_item_master_item_code ON item_master(item_code)
                """))
            except:
                print("    Index on item_code already exists")
            
            db.session.commit()
            print("✓ item_master schema migration completed")
            
        except Exception as e:
            print(f"✗ Error migrating item_master: {e}")
            db.session.rollback()
            raise

def migrate_recipe_master_schema(app):
    """Transform recipe_master to flexible component schema"""
    print("Migrating recipe_master table schema...")
    
    with app.app_context():
        try:
            # Step 1: Create new recipe_master table with flexible component system
            print("  - Creating new recipe_master structure...")
            
            db.session.execute(text("""
                CREATE TABLE recipe_master_new (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    quantity_kg DECIMAL(10,4) NOT NULL,
                    recipe_wip_id INT NOT NULL,
                    component_item_id INT NOT NULL,
                    FOREIGN KEY (recipe_wip_id) REFERENCES item_master(id),
                    FOREIGN KEY (component_item_id) REFERENCES item_master(id),
                    UNIQUE KEY uq_recipe_component (recipe_wip_id, component_item_id)
                )
            """))
            
            # Step 2: Migrate data from old to new structure
            print("  - Migrating recipe data...")
            
            # Check what columns exist in current recipe_master
            current_columns = []
            try:
                result = db.session.execute(text("DESCRIBE recipe_master"))
                current_columns = [row[0] for row in result.fetchall()]
            except:
                print("    Could not describe current recipe_master table")
            
            # Build the INSERT query based on available columns
            if 'kg_per_batch' in current_columns and 'finished_good_id' in current_columns and 'raw_material_id' in current_columns:
                # Standard old schema
                db.session.execute(text("""
                    INSERT INTO recipe_master_new (quantity_kg, recipe_wip_id, component_item_id)
                    SELECT 
                        COALESCE(kg_per_batch, 0) as quantity_kg,
                        finished_good_id as recipe_wip_id,
                        raw_material_id as component_item_id
                    FROM recipe_master
                    WHERE finished_good_id IS NOT NULL 
                    AND raw_material_id IS NOT NULL
                """))
            elif 'quantity_kg' in current_columns and 'recipe_wip_id' in current_columns and 'component_rm_id' in current_columns:
                # Previous migration schema
                db.session.execute(text("""
                    INSERT INTO recipe_master_new (quantity_kg, recipe_wip_id, component_item_id)
                    SELECT 
                        quantity_kg,
                        recipe_wip_id,
                        component_rm_id as component_item_id
                    FROM recipe_master
                    WHERE recipe_wip_id IS NOT NULL 
                    AND component_rm_id IS NOT NULL
                """))
            else:
                print("    Warning: Unrecognized recipe_master schema, skipping data migration")
            
            # Step 3: Replace old table with new one
            print("  - Replacing old recipe_master table...")
            
            db.session.execute(text("DROP TABLE recipe_master"))
            db.session.execute(text("RENAME TABLE recipe_master_new TO recipe_master"))
            
            db.session.commit()
            print("✓ recipe_master schema migration completed")
            
        except Exception as e:
            print(f"✗ Error migrating recipe_master: {e}")
            db.session.rollback()
            raise

def verify_migration(app):
    """Verify the migration was successful"""
    print("Verifying migration...")
    
    with app.app_context():
        try:
            # Check item_master structure
            result = db.session.execute(text("DESCRIBE item_master"))
            item_columns = [row[0] for row in result.fetchall()]
            
            required_item_columns = [
                'id', 'item_code', 'description', 'item_type_id', 'category',
                'department', 'machinery', 'min_stock', 'max_stock', 'is_active',
                'price_per_kg', 'is_make_to_order', 'loss_percentage', 
                'calculation_factor', 'wip_item_id', 'wipf_item_id'
            ]
            
            print("  Item Master columns:")
            for col in required_item_columns:
                if col in item_columns:
                    print(f"    ✓ {col}")
                else:
                    print(f"    ✗ {col} MISSING")
            
            # Check recipe_master structure
            result = db.session.execute(text("DESCRIBE recipe_master"))
            recipe_columns = [row[0] for row in result.fetchall()]
            
            required_recipe_columns = [
                'id', 'quantity_kg', 'recipe_wip_id', 'component_item_id'
            ]
            
            print("  Recipe Master columns:")
            for col in required_recipe_columns:
                if col in recipe_columns:
                    print(f"    ✓ {col}")
                else:
                    print(f"    ✗ {col} MISSING")
            
            # Check data counts
            item_count = db.session.execute(text("SELECT COUNT(*) FROM item_master")).scalar()
            recipe_count = db.session.execute(text("SELECT COUNT(*) FROM recipe_master")).scalar()
            
            print(f"  Data verification:")
            print(f"    ✓ Items: {item_count}")
            print(f"    ✓ Recipes: {recipe_count}")
            
            # Test flexible component system
            print("  Testing flexible component relationships:")
            component_types = db.session.execute(text("""
                SELECT 
                    it.type_name,
                    COUNT(*) as component_count
                FROM recipe_master r
                JOIN item_master i ON r.component_item_id = i.id
                JOIN item_type it ON i.item_type_id = it.id
                GROUP BY it.type_name
            """)).fetchall()
            
            for type_name, count in component_types:
                print(f"    ✓ {type_name} components: {count}")
            
        except Exception as e:
            print(f"✗ Verification error: {e}")

def main():
    """Main migration function"""
    print("=" * 60)
    print("Database Migration: Flexible Component Schema")
    print("=" * 60)
    print(f"Started at: {datetime.now()}")
    
    app = create_app()
    
    try:
        # Step 1: Create backups
        backup_tables(app)
        
        # Step 2: Migrate item_master
        migrate_item_master_schema(app)
        
        # Step 3: Migrate recipe_master
        migrate_recipe_master_schema(app)
        
        # Step 4: Verify migration
        verify_migration(app)
        
        print("\n" + "=" * 60)
        print("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"Completed at: {datetime.now()}")
        print("\nYour database now supports flexible component relationships.")
        print("Recipe components can now be RM, WIP, or other item types.")
        print("\nBackup tables created:")
        print("- item_master_backup_flexible_schema")  
        print("- recipe_master_backup_flexible_schema")
        
    except Exception as e:
        print(f"\n❌ MIGRATION FAILED: {e}")
        print("\nTo restore from backup if needed:")
        print("- DROP TABLE item_master; RENAME TABLE item_master_backup_flexible_schema TO item_master;")
        print("- DROP TABLE recipe_master; RENAME TABLE recipe_master_backup_flexible_schema TO recipe_master;")
        sys.exit(1)

if __name__ == "__main__":
    main() 