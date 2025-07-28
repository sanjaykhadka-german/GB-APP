from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mysql://user:password@localhost/composite_key_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Import models after db initialization
from models.item_master import ItemMaster, ItemType, Category, Department, UOM
from models.recipe_master import RecipeMaster

# Import controllers
from controllers.item_controller import item_bp
from controllers.recipe_controller import recipe_bp

# Register blueprints
app.register_blueprint(item_bp, url_prefix='/api/items')
app.register_blueprint(recipe_bp, url_prefix='/api/recipes')

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/items')
def items_page():
    """Items management page"""
    return render_template('items/index.html')

@app.route('/recipes')
def recipes_page():
    """Recipes management page"""
    return render_template('recipes/index.html')

@app.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)