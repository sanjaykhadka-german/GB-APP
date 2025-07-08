from app import app, db
from models.soh import SOH
from models.raw_material_stocktake import RawMaterialStocktake
from models.packing import Packing
from models.filling import Filling
from models.production import Production
from models.usage_report_table import UsageReportTable
from models.raw_material_report import RawMaterialReport

def verify_tables_empty():
    with app.app_context():
        try:
            # Check each table
            tables = {
                'SOH': SOH.query.count(),
                'Raw Material Stocktake': RawMaterialStocktake.query.count(),
                'Packing': Packing.query.count(),
                'Filling': Filling.query.count(),
                'Production': Production.query.count(),
                'Usage Report': UsageReportTable.query.count(),
                'Raw Material Report': RawMaterialReport.query.count()
            }
            
            all_empty = True
            print("\nTable Status:")
            print("-" * 40)
            for table_name, count in tables.items():
                status = "EMPTY" if count == 0 else f"NOT EMPTY ({count} records)"
                print(f"{table_name:25} | {status}")
                if count > 0:
                    all_empty = False
            print("-" * 40)
            
            if all_empty:
                print("\n✅ All tables are empty and ready for new data.")
            else:
                print("\n⚠️  Some tables still have data. Please check the SQL truncate operation.")
                
        except Exception as e:
            print(f"\n❌ Error checking tables: {str(e)}")

if __name__ == "__main__":
    verify_tables_empty() 