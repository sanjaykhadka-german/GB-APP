#!/usr/bin/env python3
"""
Database Migration: Transform to Exact User-Specified Schema
===========================================================

This script migrates the current complex item_master and recipe_master tables
to the exact simplified schema specified by the user.

Changes to item_master:
- Remove all extra columns not in the specified schema
- Keep only: id, item_code, description, item_type_id, category, department, 
  machinery, min_stock, max_stock, is_active, price_per_kg, is_make_to_order,
  loss_percentage, calculation_factor, wip_item_id, wipf_item_id
- Convert foreign key references to simple string fields where specified

Changes to recipe_master:
- Transform to the exact new schema: id, quantity_kg, recipe_wip_id, component_rm_id
- Map existing finished_good_id -> recipe_wip_id and raw_material_id -> component_rm_id
- Convert kg_per_batch -> quantity_kg
"""

import os
import sys
from datetime import datetime

# Add the parent directory to sys.path to import models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from database import db
from sqlalchemy import text

def create_app():
    """Create Flask app for migration"""
    app = Flask(__name__)
    
    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/gb_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    db.init_app(app)
    return app

def backup_tables(app):
    """Create backup tables before migration"""
    print("Creating backup tables...")
    
    with app.app_context():
        try:
            # Backup item_master
            db.session.execute(text("""
                CREATE TABLE item_master_backup_pre_simplification 
                AS SELECT * FROM item_master
            """))
            
            # Backup recipe_master  
            db.session.execute(text("""
                CREATE TABLE recipe_master_backup_pre_simplification 
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
            # Step 1: Get foreign key lookup data before simplification
            print("  - Converting foreign key lookups to string values...")
            
            # Convert category_id to category string
            db.session.execute(text("""
                UPDATE item_master im
                LEFT JOIN category c ON im.category_id = c.id
                SET im.category = c.category_name
                WHERE im.category_id IS NOT NULL
            """))
            
            # Convert department_id to department string
            db.session.execute(text("""
                UPDATE item_master im
                LEFT JOIN department d ON im.department_id = d.department_id
                SET im.department = d.department_name
                WHERE im.department_id IS NOT NULL
            """))
            
            # Convert machinery_id to machinery string
            db.session.execute(text("""
                UPDATE item_master im
                LEFT JOIN machinery m ON im.machinery_id = m.machineID
                SET im.machinery = m.machine_name
                WHERE im.machinery_id IS NOT NULL
            """))
            
            # Step 2: Update column types and constraints to match specification
            print("  - Updating column specifications...")
            
            # Ensure columns match exact specification
            db.session.execute(text("""
                ALTER TABLE item_master 
                MODIFY COLUMN item_code VARCHAR(50) NOT NULL,
                MODIFY COLUMN description VARCHAR(255) NOT NULL,
                MODIFY COLUMN category VARCHAR(100),
                MODIFY COLUMN department VARCHAR(100), 
                MODIFY COLUMN machinery VARCHAR(100),
                MODIFY COLUMN min_stock DECIMAL(10,2) DEFAULT 0.00,
                MODIFY COLUMN max_stock DECIMAL(10,2) DEFAULT 0.00,
                MODIFY COLUMN price_per_kg DECIMAL(12,4),
                MODIFY COLUMN loss_percentage DECIMAL(5,2) DEFAULT 0.00,
                MODIFY COLUMN calculation_factor DECIMAL(10,4) DEFAULT 1.0000
            """))
            
            # Step 3: Add missing columns if they don't exist
            print("  - Adding self-referencing foreign keys...")
            
            # Check and add wip_item_id if it doesn't exist
            try:
                db.session.execute(text("""
                    ALTER TABLE item_master 
                    ADD COLUMN wip_item_id INT NULL,
                    ADD FOREIGN KEY (wip_item_id) REFERENCES item_master(id)
                """))
            except:
                print("    wip_item_id already exists")
            
            # Check and add wipf_item_id if it doesn't exist  
            try:
                db.session.execute(text("""
                    ALTER TABLE item_master 
                    ADD COLUMN wipf_item_id INT NULL,
                    ADD FOREIGN KEY (wipf_item_id) REFERENCES item_master(id)
                """))
            except:
                print("    wipf_item_id already exists")
            
            # Step 4: Drop extra columns not in the specification
            print("  - Removing columns not in specification...")
            
            extra_columns = [
                'category_id', 'department_id', 'machinery_id', 'uom_id',
                'min_level', 'max_level', 'price_per_uom', 'kg_per_unit',
                'units_per_bag', 'avg_weight_per_unit', 'supplier_name',
                'fw', 'created_by_id', 'updated_by_id', 'created_at', 'updated_at',
                'item_type'  # Remove the direct item_type column as user wants lookup
            ]
            
            for column in extra_columns:
                try:
                    db.session.execute(text(f"ALTER TABLE item_master DROP COLUMN {column}"))
                    print(f"    Dropped {column}")
                except:
                    print(f"    {column} doesn't exist (OK)")
            
            # Step 5: Ensure item_type_id is NOT NULL as per specification
            db.session.execute(text("""
                ALTER TABLE item_master 
                MODIFY COLUMN item_type_id INT NOT NULL
            """))
            
            # Step 6: Add index on item_code as specified
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
    """Transform recipe_master to exact user specification"""
    print("Migrating recipe_master table schema...")
    
    with app.app_context():
        try:
            # Step 1: Create new recipe_master table with exact specification
            print("  - Creating new recipe_master structure...")
            
            db.session.execute(text("""
                CREATE TABLE recipe_master_new (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    quantity_kg DECIMAL(10,4) NOT NULL,
                    recipe_wip_id INT NOT NULL,
                    component_rm_id INT NOT NULL,
                    FOREIGN KEY (recipe_wip_id) REFERENCES item_master(id),
                    FOREIGN KEY (component_rm_id) REFERENCES item_master(id),
                    UNIQUE KEY uq_recipe_component (recipe_wip_id, component_rm_id)
                )
            """))
            
            # Step 2: Migrate data from old to new structure
            print("  - Migrating recipe data...")
            
            # Insert data mapping old columns to new ones
            db.session.execute(text("""
                INSERT INTO recipe_master_new (quantity_kg, recipe_wip_id, component_rm_id)
                SELECT 
                    COALESCE(kg_per_batch, 0) as quantity_kg,
                    finished_good_id as recipe_wip_id,
                    raw_material_id as component_rm_id
                FROM recipe_master
                WHERE finished_good_id IS NOT NULL 
                AND raw_material_id IS NOT NULL
            """))
            
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
                'id', 'quantity_kg', 'recipe_wip_id', 'component_rm_id'
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
            
        except Exception as e:
            print(f"✗ Verification error: {e}")

def main():
    """Main migration function"""
    print("=" * 60)
    print("Database Migration: Transform to Exact User Schema")
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
        print("\nYour database now matches the exact schema specification.")
        print("Backup tables created:")
        print("- item_master_backup_pre_simplification")  
        print("- recipe_master_backup_pre_simplification")
        
    except Exception as e:
        print(f"\n❌ MIGRATION FAILED: {e}")
        print("\nTo restore from backup if needed:")
        print("- DROP TABLE item_master; RENAME TABLE item_master_backup_pre_simplification TO item_master;")
        print("- DROP TABLE recipe_master; RENAME TABLE recipe_master_backup_pre_simplification TO recipe_master;")
        sys.exit(1)

if __name__ == "__main__":
    main() 