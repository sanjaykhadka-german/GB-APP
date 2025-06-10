from database import db
from models import UsageReport
from app import app

def update_usage_report_percentages():
    try:
        # Get all usage reports
        reports = UsageReport.query.all()
        
        # Update each report's percentage
        for report in reports:
            if report.percentage is not None:
                report.percentage = report.percentage * 100
        
        # Commit the changes
        db.session.commit()
        print("Successfully updated all usage report percentages")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating usage report percentages: {str(e)}")

if __name__ == "__main__":
    with app.app_context():
        update_usage_report_percentages() 