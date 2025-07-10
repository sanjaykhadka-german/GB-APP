from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_migrate import Migrate
from database import db

# Import controllers that actually exist
from controllers.category_controller import category_bp
from controllers.department_controller import department_bp
from controllers.machinery_controller import machinery_bp
from controllers.item_master_controller import item_master_bp
from controllers.recipe_controller import recipe_bp
from controllers.production_controller import production_bp
from controllers.packing_controller import packing
from controllers.filling_controller import filling_bp
from controllers.inventory_controller import inventory_bp
from controllers.item_type_controller import item_type_bp
from controllers.soh_controller import soh_bp
from controllers.login_controller import login_bp
from controllers.ingredients_controller import ingredients_bp
from controllers.uom_controller import uom_bp

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:german@localhost/gbdb'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)

    # Register blueprints
    app.register_blueprint(login_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(department_bp)
    app.register_blueprint(machinery_bp)
    app.register_blueprint(item_master_bp)
    app.register_blueprint(recipe_bp)
    app.register_blueprint(production_bp)
    app.register_blueprint(packing)
    app.register_blueprint(filling_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(item_type_bp)
    app.register_blueprint(soh_bp)
    app.register_blueprint(ingredients_bp)
    app.register_blueprint(uom_bp)

    # Authentication middleware
    @app.before_request
    def require_login():
        # Allow access to login, register, and static files without authentication
        allowed_routes = ['login.login', 'login.register', 'login.check_username', 'login.check_email', 'static']
        
        if request.endpoint in allowed_routes:
            return
        
        # Check if user is logged in
        if 'user_id' not in session:
            # For AJAX requests, return JSON error instead of redirect
            if request.is_json or request.headers.get('Content-Type') == 'application/json':
                return jsonify({'success': False, 'error': 'Authentication required. Please log in.'}), 401
            return redirect(url_for('login.login'))

    @app.route('/')
    def index():
        return render_template('index.html', current_page="home")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)