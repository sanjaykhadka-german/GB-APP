from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:german@localhost/gbdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

with app.app_context():
    try:
        # First, get count of FG items
        count_query = text("""
            SELECT COUNT(*) as count 
            FROM item_master 
            WHERE item_code LIKE 'FG%';
        """)
        count_result = db.session.execute(count_query).scalar()
        print(f"\nFound {count_result} items with item_code starting with 'FG'")
        
        if count_result > 0:
            # Delete FG items
            delete_query = text("""
                DELETE FROM item_master 
                WHERE item_code LIKE 'FG%';
            """)
            result = db.session.execute(delete_query)
            db.session.commit()
            print(f"Successfully deleted {result.rowcount} items from item_master")
        else:
            print("No items found to delete")
            
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}") 