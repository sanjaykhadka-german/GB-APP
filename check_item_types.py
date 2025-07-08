#!/usr/bin/env python3
"""
Script to check item types in the database and identify any mismatches
"""

import os
import sys
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from database import db
from models.item_type import ItemType
from models.item_master import ItemMaster
from app import app, create_app
from models.department import Department
from models.machinery import Machinery

def check_item_types():
    """Check item types and their assignments"""
    # Get all item types
    item_types = ItemType.query.all()
    print(f"\nFound {len(item_types)} item types:")
    
    for item_type in item_types:
        print(f"\nType: {item_type.type_name}")
        items = ItemMaster.query.filter_by(item_type_id=item_type.id).all()
        print(f"Items of this type: {len(items)}")
        
        for item in items:
            print(f"\n- Item: {item.item_code}")
            print(f"  Description: {item.description}")
            print(f"  Department: {item.department.departmentName if item.department else 'None'}")
            print(f"  Machine: {item.machinery.machineryName if item.machinery else 'None'}")
            
            if item_type.type_name == 'FG':
                print(f"  WIP Item: {item.wip_item.item_code if item.wip_item else 'None'}")
                print(f"  WIPF Item: {item.wipf_item.item_code if item.wipf_item else 'None'}")
                
                if item.wip_item:
                    print(f"  WIP Department: {item.wip_item.department.departmentName if item.wip_item.department else 'None'}")
                    print(f"  WIP Machine: {item.wip_item.machinery.machineryName if item.wip_item.machinery else 'None'}")
                
                if item.wipf_item:
                    print(f"  WIPF Department: {item.wipf_item.department.departmentName if item.wipf_item.department else 'None'}")
                    print(f"  WIPF Machine: {item.wipf_item.machinery.machineryName if item.wipf_item.machinery else 'None'}")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        check_item_types() 