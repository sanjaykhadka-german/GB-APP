from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from dotenv import load_dotenv
import os
import sqlalchemy.exc
from datetime import datetime
from flask_migrate import Migrate

# Import the single SQLAlchemy instance
from database import db


def create_app():
    # Load environment variables from .env file
    load_dotenv()

    # File upload configuration
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

    

    # Create uploads directory if it doesn't exist
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    # Create and configure the Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret-key')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # Validate SQLALCHEMY_DATABASE_URI
    if not app.config['SQLALCHEMY_DATABASE_URI']:
        raise RuntimeError(
            "SQLALCHEMY_DATABASE_URI is not set. Please define it in the .env file or environment variables."
        )

    # Initialize SQLAlchemy with the app
    db.init_app(app)
    migrate = Migrate(app, db)

    # Register Blueprints
    from controllers.joining_controller import joining_bp
    from controllers.soh_controller import soh_bp
    from controllers.packing_controller import packing
    from controllers.filling_controller import filling_bp
    from controllers.production_controller import production_bp
    from controllers.recipe_controller import recipe_bp
    from controllers.production_plan_controller import production_plan_bp
    from controllers.inject_products_controller import injected_products_bp
    from controllers.raw_materials_controller import raw_materials_bp
    from controllers.inventory_controller import inventory_bp
    from controllers.department_controller import department_bp
    from controllers.machinery_controller import machinery_bp
    from controllers.category_controller import category_bp
    from controllers.item_master_controller import item_master_bp

    app.register_blueprint(joining_bp)
    app.register_blueprint(soh_bp)
    app.register_blueprint(packing)
    app.register_blueprint(filling_bp)
    app.register_blueprint(production_bp)
    app.register_blueprint(recipe_bp)
    app.register_blueprint(production_plan_bp, url_prefix='/production_plan')
    app.register_blueprint(injected_products_bp)
    app.register_blueprint(raw_materials_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(department_bp)
    app.register_blueprint(machinery_bp)    
    app.register_blueprint(category_bp)
    app.register_blueprint(item_master_bp)

    # Import models
    from models import soh, finished_goods, item_master, recipe_master, usage_report
    from models import machinery, department, category, production, packing, filling, allergen, joining_allergen
    from models import RawMaterials
    

    @app.template_filter('format_date')
    def format_date(value):
        return value.strftime('%Y-%m-%d') if value else ''
    
    # Define routes
    @app.route('/') 
    def index():
        return render_template('index.html', current_page="home")

    

    # Create database tables within app context
    with app.app_context():
        db.create_all()

    return app

# Create the app
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)