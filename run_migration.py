#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv
from flask import Flask
from flask_migrate import Migrate
from database import db
from models.packing import Packing
from models.soh import SOH
from models.machinery import Machinery
from models.filling import Filling
from models.production import Production
from models.recipe_master import RecipeMaster
from models.raw_materials import RawMaterials
from models.usage_report_table import UsageReportTable
from models.raw_material_report import RawMaterialReport
from models.item_master import ItemMaster
from sqlalchemy import text

# Create Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:password@localhost/gb_app'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)

if __name__ == '__main__':
    with app.app_context():
        # Run the migration
        os.system('alembic upgrade head') 