from app import create_app, db
from models.department import Department
from models.machinery import Machinery
from models.item_master import ItemMaster

def check_departments():
    """Check departments and machinery in the database"""
    # Get all departments
    departments = Department.query.all()
    print(f"\nFound {len(departments)} departments:")
    for dept in departments:
        print(f"- ID: {dept.department_id}, Name: {dept.departmentName}")
        
        # Get items in this department
        items = ItemMaster.query.filter_by(department_id=dept.department_id).all()
        print(f"  Items in department: {len(items)}")
    
    # Get all machinery
    machines = Machinery.query.all()
    print(f"\nFound {len(machines)} machines:")
    for machine in machines:
        print(f"- ID: {machine.machineID}, Name: {machine.machineryName}")
        
        # Get items using this machine
        items = ItemMaster.query.filter_by(machinery_id=machine.machineID).all()
        print(f"  Items using machine: {len(items)}")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        check_departments() 