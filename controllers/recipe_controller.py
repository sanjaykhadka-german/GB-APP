from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy.sql import text
from decimal import Decimal
import sqlalchemy.exc
from datetime import datetime

# Create a Blueprint for recipe routes
recipe_bp = Blueprint('recipe', __name__, template_folder='templates')

@recipe_bp.route('/recipe_search', methods=['GET'])
def recipe_search():
    from app import db  # Import db here to avoid circular import
    from models import RecipeMaster  # Import RecipeMaster for searching recipes

    search_recipe_code = request.args.get('recipe_code', '')
    search_description = request.args.get('description', '')

    return render_template('recipe/recipe_search.html', 
                         search_recipe_code=search_recipe_code,
                         search_description=search_description)

@recipe_bp.route('/recipe_add', methods=['GET', 'POST'])
def recipe_add():
    from app import db  # Import db here to avoid circular import
    from models import RecipeMaster

    if request.method == 'POST':
        recipe_code = request.form.get('recipe_code')
        description = request.form.get('description')
        raw_material = request.form.get('raw_material')
        kg_per_batch = request.form.get('kg_per_batch')

        try:
            if not all([recipe_code, description, raw_material, kg_per_batch]):
                flash("All fields are required.", 'error')
                return render_template('recipe/recipe_add.html', recipes=RecipeMaster.query.all())

            kg_per_batch = Decimal(kg_per_batch)
            # Calculate total kg_per_batch for the description (excluding the current entry being added)
            total_kg_for_description = db.session.query(db.func.sum(RecipeMaster.kg_per_batch))\
                .filter(RecipeMaster.description == description)\
                .scalar()
            total_kg_for_description = float(total_kg_for_description) if total_kg_for_description else 0.0
            total_kg_with_new = total_kg_for_description + float(kg_per_batch)
            percentage = (float(kg_per_batch) / total_kg_with_new) * 100 if total_kg_with_new else 0

            new_recipe = RecipeMaster(
                recipe_code=recipe_code,
                description=description,
                raw_material=raw_material,
                kg_per_batch=kg_per_batch,
                percentage=Decimal(percentage)
            )

            db.session.add(new_recipe)
            db.session.commit()

            # Update percentages for all recipes with the same description
            recipes_to_update = RecipeMaster.query.filter(RecipeMaster.description == description).all()
            for recipe in recipes_to_update:
                recipe.percentage = (float(recipe.kg_per_batch) / total_kg_with_new) * 100
            db.session.commit()

            flash("Recipe added successfully!", 'success')
            return redirect(url_for('recipe.recipe_add'))

        except ValueError:
            flash("Invalid input. Please check your data.", 'error')
            db.session.rollback()
            recipes = RecipeMaster.query.all()
            return render_template('recipe/recipe_add.html', recipes=recipes)

        except sqlalchemy.exc.IntegrityError as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", 'error')
            recipes = RecipeMaster.query.all()
            return render_template('recipe/recipe_add.html', recipes=recipes)

        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred: {str(e)}", 'error')
            recipes = RecipeMaster.query.all()
            return render_template('recipe/recipe_add.html', recipes=recipes)
    
    recipes = RecipeMaster.query.all()
    return render_template('recipe/recipe_add.html', recipes=recipes)

@recipe_bp.route('/autocomplete_recipe', methods=['GET'])
def autocomplete_recipe():
    from app import db  # Import db here to avoid circular import
    from models import RecipeMaster

    search = request.args.get('query', '').strip()

    if not search:
        return jsonify([])

    try:
        query = text("SELECT recipe_code, description FROM recipe_master WHERE recipe_code LIKE :search LIMIT 10")
        results = db.session.execute(query, {"search": search + "%"}).fetchall()
        suggestions = [{"recipe_code": row[0], "description": row[1]} for row in results]
        return jsonify(suggestions)
    except Exception as e:
        print("Error fetching recipe autocomplete suggestions:", e)
        return jsonify([])

@recipe_bp.route('/get_search_recipes', methods=['GET'])
def get_search_recipes():
    from app import db  # Import db here to avoid circular import
    from models import RecipeMaster

    search_recipe_code = request.args.get('recipe_code', '').strip()
    search_description = request.args.get('description', '').strip()

    recipes_query = RecipeMaster.query

    if search_recipe_code:
        recipes_query = recipes_query.filter(RecipeMaster.recipe_code.ilike(f"%{search_recipe_code}%"))
    if search_description:
        recipes_query = recipes_query.filter(RecipeMaster.description.ilike(f"%{search_description}%"))

    recipes = recipes_query.all()

    recipes_data = [
        {
            "recipe_code": recipe.recipe_code,
            "description": recipe.description,
            "raw_material": recipe.raw_material,
            "kg_per_batch": float(recipe.kg_per_batch),  # Convert Decimal to float for JSON serialization
            "percentage": float(recipe.percentage) if recipe.percentage else 0.0
        }
        for recipe in recipes
    ]

    return jsonify(recipes_data)

@recipe_bp.route('/usage', methods=['GET'])
def usage():
    from app import db  # Import db here to avoid circular import
    from models import Production, RecipeMaster

    # Fetch all production records
    productions = Production.query.all()

    usage_data = []

    for production in productions:
        # Find all recipe entries for the production_code
        recipes = RecipeMaster.query.filter_by(recipe_code=production.production_code).all()

        # If no recipes found for this production code, skip
        if not recipes:
            continue

        # Calculate usage for each raw material
        for recipe in recipes:
            usage = float(production.total_kg) * (float(recipe.percentage) / 100)
            usage_data.append({
                'production_date': production.production_date.strftime('%d/%m/%Y'),
                'recipe_code': production.production_code,
                'raw_material': recipe.raw_material,
                'usage': round(usage, 2),
                'percentage': float(recipe.percentage)
            })

    return render_template('recipe/usage.html', usage_data=usage_data)

@recipe_bp.route('/raw_material_report', methods=['GET'])
def raw_material_report():
    from app import db  # Import db here to avoid circular import
    from models import Production, RecipeMaster

    # Step 1: Calculate the Usage Table (same as /usage route)
    productions = Production.query.all()
    usage_data = []

    for production in productions:
        recipes = RecipeMaster.query.filter_by(recipe_code=production.production_code).all()
        if not recipes:
            continue
        for recipe in recipes:
            usage = float(production.total_kg) * (float(recipe.percentage) / 100)
            usage_data.append({
                'production_date': production.production_date.strftime('%d/%m/%Y'),
                'recipe_code': production.production_code,
                'raw_material': recipe.raw_material,
                'usage': round(usage, 2),
                'percentage': float(recipe.percentage)
            })

    # Step 2: Aggregate by Raw Material
    raw_material_totals = {}
    for entry in usage_data:
        raw_material = entry['raw_material']
        usage = entry['usage']
        if raw_material in raw_material_totals:
            raw_material_totals[raw_material] += usage
        else:
            raw_material_totals[raw_material] = usage

    # Convert to list of dictionaries for the template
    raw_material_data = [
        {'raw_material': material, 'meat_required': round(total, 2)}
        for material, total in raw_material_totals.items()
    ]

    # Sort by raw material name for better readability
    raw_material_data.sort(key=lambda x: x['raw_material'])

    return render_template('recipe/raw_material.html', raw_material_data=raw_material_data)