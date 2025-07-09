from app import app, db
from models.inventory import Inventory
from models.raw_material_report_table import RawMaterialReportTable
from models.usage_report_table import UsageReportTable

def update_inventory():
    with app.app_context():
        try:
            print("Updating inventory records with report data...")
            
            # Get all inventory records
            inventories = Inventory.query.all()
            
            for inv in inventories:
                # Get report data
                report = RawMaterialReportTable.query.filter_by(
                    week_commencing=inv.week_commencing,
                    item_id=inv.item_id
                ).first()
                
                # Get usage data
                usage = UsageReportTable.query.filter_by(
                    week_commencing=inv.week_commencing,
                    item_id=inv.item_id
                ).first()
                
                if report:
                    inv.required_total_production = report.required_total_production
                    inv.value_required_rm = report.value_required_rm
                    inv.required_for_plan = report.required_for_plan
                    inv.variance_week = report.variance_week
                    inv.variance = report.variance
                
                if usage:
                    inv.kg_required = usage.monday
                
                # Calculate to_be_ordered and closing_stock
                if inv.variance_week < 0:
                    inv.to_be_ordered = abs(inv.variance_week)
                    inv.closing_stock = 0
                else:
                    inv.to_be_ordered = 0
                    inv.closing_stock = inv.variance_week
            
            db.session.commit()
            print("Inventory records updated successfully!")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    update_inventory() 