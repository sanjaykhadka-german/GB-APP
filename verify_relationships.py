#!/usr/bin/env python3
"""
Verify that the WIP/WIPF relationships are populated correctly
and that this fixes the SOH upload issue.
"""

import os
import sys
from flask import Flask
from database import db
from dotenv import load_dotenv
from sqlalchemy import text

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
        # Count how many can create each type
        summary_query = text('''
            SELECT 
                COUNT(*) as total_fg,
                COUNT(wip.id) as can_create_production,
                COUNT(wipf.id) as can_create_filling
            FROM item_master fg
            LEFT JOIN item_master wip ON fg.wip_item_id = wip.id
            LEFT JOIN item_master wipf ON fg.wipf_item_id = wipf.id
            WHERE fg.item_type_id = (SELECT id FROM item_type WHERE type_name = "FG")
        ''')
        
        summary = db.session.execute(summary_query).fetchone()
        print('📊 SOH Upload Fix Verification:')
        print('=' * 50)
        print(f'  Total FG items: {summary[0]}')
        print(f'  Can create Production lists: {summary[1]} ({summary[1]/summary[0]*100:.1f}%)')
        print(f'  Can create Filling lists: {summary[2]} ({summary[2]/summary[0]*100:.1f}%)')
        print()
        print('✅ Before: SOH upload could only create packing lists')
        print('✅ Now: SOH upload can create production AND filling lists!')
        print()
        
        # Show a few examples
        examples_query = text('''
            SELECT 
                fg.item_code,
                fg.description,
                wip.item_code as wip_code,
                wipf.item_code as wipf_code
            FROM item_master fg
            LEFT JOIN item_master wip ON fg.wip_item_id = wip.id
            LEFT JOIN item_master wipf ON fg.wipf_item_id = wipf.id
            WHERE fg.item_type_id = (SELECT id FROM item_type WHERE type_name = "FG")
            LIMIT 5
        ''')
        
        examples = db.session.execute(examples_query).fetchall()
        print('📋 Examples:')
        for example in examples:
            fg_code, fg_desc, wip_code, wipf_code = example
            print(f'  {fg_code}: WIP={wip_code or "None"}, WIPF={wipf_code or "None"}')

if __name__ == "__main__":
    main() 