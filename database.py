from flask_sqlalchemy import SQLAlchemy
from flask import current_app

db = SQLAlchemy()

def init_db(app):
    """Initialize the database with the app"""
    db.init_app(app)
    with app.app_context():
        db.create_all()