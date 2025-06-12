from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:german@localhost/gbdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

with app.app_context():
    try:
        # Step 1: Truncate recipe_master table
        truncate_query = text("TRUNCATE TABLE recipe_master;")
        db.session.execute(truncate_query)
        print("\nSuccessfully truncated recipe_master table")
        
        # Step 2: Delete FG items from item_master
        delete_query = text("""
            DELETE FROM item_master 
            WHERE item_code LIKE 'FG%';
        """)
        result = db.session.execute(delete_query)
        db.session.commit()
        print(f"Successfully deleted {result.rowcount} FG items from item_master")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}") 