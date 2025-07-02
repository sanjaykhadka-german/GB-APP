from app import app, db
from sqlalchemy import text

def verify_filling():
    with app.app_context():
        try:
            result = db.session.execute(text("DESCRIBE filling"))
            print("\nFilling table structure:")
            for row in result:
                print(row)

        except Exception as e:
            print(f"Error verifying filling table: {str(e)}")

if __name__ == '__main__':
    verify_filling() 