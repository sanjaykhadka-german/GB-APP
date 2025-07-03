#!/usr/bin/env python3
"""
Test script to verify the ItemType-ItemMaster relationship fix.
"""

import os
import sys
from flask import Flask
from database import db
from dotenv import load_dotenv
from models.item_master import ItemMaster
from models.item_type import ItemType

def setup_app():
    load_dotenv()
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def main():
    app = setup_app()
    
    with app.app_context():
        try:
            print("🔍 Testing ItemType-ItemMaster relationship fix...")
            
            # Test ItemType query
            item_types = ItemType.query.limit(3).all()
            print('✅ ItemType query successful')
            
            for item_type in item_types:
                print(f'   - {item_type.type_name}: {len(item_type.items)} items')
            
            # Test ItemMaster query
            items = ItemMaster.query.limit(3).all()
            print('✅ ItemMaster query successful')
            
            for item in items:
                print(f'   - {item.item_code}: {item.item_type.type_name}')
                
            print('✅ All relationship tests passed!')
            print('✅ The SQLAlchemy error should now be fixed!')
            
        except Exception as e:
            print(f'❌ Error: {e}')
            print('❌ The relationship fix may need further adjustment.')

if __name__ == "__main__":
    main() 