from flask import Flask
from database import db
from sqlalchemy.sql import text
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', 'mysql://admin:admin@localhost/gb_app')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def check_tables():
    with app.app_context():
        try:
            # Check all relevant tables
            tables_to_check = [
                'raw_material_report',
                'raw_material_report_table',
                'usage_report',
                'usage_report_table'
            ]
            
            print("\nChecking tables in database...")
            for table in tables_to_check:
                check_table = text("""
                    SELECT COUNT(*) as table_exists
                    FROM information_schema.tables 
                    WHERE table_schema = DATABASE()
                    AND table_name = :table
                """)
                result = db.session.execute(check_table, {'table': table}).fetchone()
                
                if result.table_exists > 0:
                    print(f"✅ Table '{table}' exists")
                else:
                    print(f"❌ Table '{table}' does not exist")
            
            # Check which models are being used in code
            print("\nChecking model files...")
            model_files = {
                'raw_material_report.py': 'models/raw_material_report.py',
                'raw_material_report_table.py': 'models/raw_material_report_table.py',
                'usage_report.py': 'models/usage_report.py',
                'usage_report_table.py': 'models/usage_report_table.py'
            }
            
            for file_name, file_path in model_files.items():
                if os.path.exists(file_path):
                    print(f"✅ Model file '{file_name}' exists")
                else:
                    print(f"❌ Model file '{file_name}' does not exist")
                
        except Exception as e:
            print(f"❌ Error checking tables: {str(e)}")

if __name__ == "__main__":
    check_tables() 