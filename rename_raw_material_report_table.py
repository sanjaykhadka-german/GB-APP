from flask import Flask
from database import db
from sqlalchemy.sql import text
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', 'mysql://admin:admin@localhost/gb_app')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def rename_raw_material_report_table():
    with app.app_context():
        try:
            # Check if old table exists
            check_old_table = text("""
                SELECT COUNT(*) as table_exists 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
                AND table_name = 'raw_material_report'
            """)
            result = db.session.execute(check_old_table).fetchone()
            
            if result.table_exists == 0:
                print("❌ Original table 'raw_material_report' not found")
                return
            
            # Check if new table already exists
            check_new_table = text("""
                SELECT COUNT(*) as table_exists 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
                AND table_name = 'raw_material_report_table'
            """)
            result = db.session.execute(check_new_table).fetchone()
            
            if result.table_exists > 0:
                print("❌ Table 'raw_material_report_table' already exists")
                return
            
            # Rename the table
            rename_query = text("RENAME TABLE raw_material_report TO raw_material_report_table")
            db.session.execute(rename_query)
            db.session.commit()
            
            print("✅ Successfully renamed raw_material_report table to raw_material_report_table")
            
            # Verify the rename
            verify_query = text("""
                SELECT COUNT(*) as table_exists 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
                AND table_name = 'raw_material_report_table'
            """)
            result = db.session.execute(verify_query).fetchone()
            
            if result.table_exists > 0:
                print("✅ Verified: New table exists")
            else:
                print("❌ Verification failed: New table not found")
                
        except Exception as e:
            print(f"❌ Error renaming table: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    rename_raw_material_report_table() 