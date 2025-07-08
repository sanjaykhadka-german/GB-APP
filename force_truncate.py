from app import app, db
from models.soh import SOH
from models.raw_material_stocktake import RawMaterialStocktake
from models.packing import Packing
from models.filling import Filling
from models.production import Production
from models.usage_report_table import UsageReportTable
from models.raw_material_report import RawMaterialReport
from sqlalchemy import text

def force_truncate_tables():
    with app.app_context():
        try:
            # Disable foreign key checks
            db.session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            
            # List of tables to truncate
            tables = [
                SOH,
                RawMaterialStocktake,
                Packing,
                Filling,
                Production,
                UsageReportTable,
                RawMaterialReport
            ]
            
            print("\nTruncating tables...")
            print("-" * 40)
            
            # Truncate each table
            for table in tables:
                try:
                    # Get table name
                    table_name = table.__tablename__
                    
                    # Delete all records
                    db.session.query(table).delete()
                    
                    # Force execute truncate
                    db.session.execute(text(f"TRUNCATE TABLE {table_name}"))
                    
                    # Get count after truncate
                    count = db.session.query(table).count()
                    
                    status = "SUCCESS" if count == 0 else f"FAILED ({count} records remain)"
                    print(f"{table_name:25} | {status}")
                    
                except Exception as e:
                    print(f"{table_name:25} | ERROR: {str(e)}")
            
            # Commit the transaction
            db.session.commit()
            
            # Re-enable foreign key checks
            db.session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
            db.session.commit()
            
            print("-" * 40)
            print("\n✅ Truncate operation completed.")
            
        except Exception as e:
            print(f"\n❌ Error during truncate: {str(e)}")
            db.session.rollback()
        finally:
            # Make sure foreign key checks are re-enabled
            db.session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
            db.session.commit()

if __name__ == "__main__":
    force_truncate_tables() 