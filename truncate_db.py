from app import create_app, db
from models.raw_material_report_table import RawMaterialReportTable
from models.usage_report_table import UsageReportTable
from models.production import Production
from models.filling import Filling
from models.packing import Packing
from models.soh import SOH
from models.raw_material_stocktake import RawMaterialStocktake
from sqlalchemy import text

def truncate_tables():
    """Truncate all relevant tables"""
    try:
        # Disable foreign key checks
        db.session.execute(text('SET FOREIGN_KEY_CHECKS = 0'))
        
        # Truncate tables
        tables = [
            RawMaterialReportTable,
            UsageReportTable,
            Production,
            Filling,
            Packing,
            SOH,
            RawMaterialStocktake
        ]
        
        for table in tables:
            print(f"Truncating {table.__tablename__}...")
            db.session.execute(text(f'TRUNCATE TABLE {table.__tablename__}'))
            
        # Re-enable foreign key checks
        db.session.execute(text('SET FOREIGN_KEY_CHECKS = 1'))
        db.session.commit()
        
        print("\nVerifying tables are empty:")
        for table in tables:
            count = db.session.query(table).count()
            print(f"{table.__tablename__}: {count} rows")
            
        print("\nAll tables truncated successfully!")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error truncating tables: {str(e)}")
        raise

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        truncate_tables() 