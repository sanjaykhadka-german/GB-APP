from database import db
from models import RecipeMaster
from app import app  # Import the Flask app

def update_percentages():
    try:
        # Get all recipes
        recipes = RecipeMaster.query.all()
        
        # Update each recipe's percentage
        for recipe in recipes:
            if recipe.percentage is not None:
                recipe.percentage = recipe.percentage * 100
        
        # Commit the changes
        db.session.commit()
        print("Successfully updated all percentages")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating percentages: {str(e)}")

if __name__ == "__main__":
    with app.app_context():
        update_percentages() 