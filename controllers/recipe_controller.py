from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy.sql import text
from decimal import Decimal
import sqlalchemy.exc
from datetime import datetime

# Create a Blueprint for recipe routes
recipe_bp = Blueprint('recipe', __name__, template_folder='templates')

@recipe_bp.route('/recipe', methods=['GET', 'POST'])
def recipe_page():
    from database import db
    from models import RecipeMaster

    if request.method == 'POST':
        # Handle add or edit recipe form submission
        recipe_id = request.form.get('recipe_id')  # For edit case
        recipe_code = request.form.get('recipe_code')
        description = request.form.get('description')
        raw_material = request.form.get('raw_material')
        kg_per_batch = request.form.get('kg_per_batch')

        try:
            if not all([recipe_code, description, raw_material, kg_per_batch]):
                flash("All fields are required.", 'error')
                return render_template('recipe/recipe.html', 
                                     search_recipe_code=request.args.get('recipe_code', ''),
                                     search_description=request.args.get('description', ''),
                                     recipes=RecipeMaster.query.all())

            kg_per_batch = Decimal(kg_per_batch)

            if recipe_id:  # Edit case
                recipe = RecipeMaster.query.get_or_404(recipe_id)
                old_kg = float(recipe.kg_per_batch)
                recipe.recipe_code = recipe_code
                recipe.description = description
                recipe.raw_material = raw_material
                recipe.kg_per_batch = kg_per_batch
            else:  # Add case
                recipe = RecipeMaster(
                    recipe_code=recipe_code,
                    description=description,
                    raw_material=raw_material,
                    kg_per_batch=kg_per_batch,
                    percentage=Decimal(0)
                )
                db.session.add(recipe)

            db.session.flush()

            # Recalculate percentages for all recipes with the same description
            recipes_to_update = RecipeMaster.query.filter(RecipeMaster.description == description).all()
            total_kg = sum(float(r.kg_per_batch) for r in recipes_to_update)
            for r in recipes_to_update:
                r.percentage = Decimal((float(r.kg_per_batch) / total_kg) * 100) if total_kg > 0 else Decimal(0)
            db.session.commit()

            flash("Recipe saved successfully!", 'success')
            return redirect(url_for('recipe.recipe_page'))

        except ValueError:
            flash("Invalid input. Please check your data.", 'error')
            db.session.rollback()
            return render_template('recipe/recipe.html', 
                                 search_recipe_code=request.args.get('recipe_code', ''),
                                 search_description=request.args.get('description', ''),
                                 recipes=RecipeMaster.query.all())

        except sqlalchemy.exc.IntegrityError as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", 'error')
            return render_template('recipe/recipe.html', 
                                 search_recipe_code=request.args.get('recipe_code', ''),
                                 search_description=request.args.get('description', ''),
                                 recipes=RecipeMaster.query.all())

        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred: {str(e)}", 'error')
            return render_template('recipe/recipe.html', 
                                 search_recipe_code=request.args.get('recipe_code', ''),
                                 search_description=request.args.get('description', ''),
                                 recipes=RecipeMaster.query.all())

    # GET request: render the page or edit form
    search_recipe_code = request.args.get('recipe_code', '')
    search_description = request.args.get('description', '')
    edit_id = request.args.get('edit_id')
    if edit_id:
        recipe = RecipeMaster.query.get_or_404(edit_id)
        return render_template('recipe/recipe.html', 
                             search_recipe_code=search_recipe_code,
                             search_description=search_description,
                             recipes=RecipeMaster.query.all(),
                             edit_recipe=recipe)
    return render_template('recipe/recipe.html', 
                         search_recipe_code=search_recipe_code,
                         search_description=search_description,
                         recipes=RecipeMaster.query.all())

@recipe_bp.route('/recipe/delete/<int:id>', methods=['POST'])
def delete_recipe(id):
    from database import db
    from models import RecipeMaster
    try:
        recipe = RecipeMaster.query.get_or_404(id)
        description = recipe.description
        db.session.delete(recipe)
        db.session.commit()

        # Recalculate percentages for remaining recipes with the same description
        recipes_to_update = RecipeMaster.query.filter(RecipeMaster.description == description).all()
        if recipes_to_update:
            total_kg = sum(float(r.kg_per_batch) for r in recipes_to_update)
            for r in recipes_to_update:
                r.percentage = Decimal((float(r.kg_per_batch) / total_kg) * 100) if total_kg > 0 else Decimal(0)
            db.session.commit()

        flash("Recipe deleted successfully!", 'success')
        return redirect(url_for('recipe.recipe_page'))
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", 'error')
        return redirect(url_for('recipe.recipe_page'))

@recipe_bp.route('/autocomplete_recipe', methods=['GET'])
def autocomplete_recipe():
    from database import db
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
    from database import db
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
            "kg_per_batch": float(recipe.kg_per_batch),
            "percentage": float(recipe.percentage) if recipe.percentage else 0.0,
            "id": recipe.id  # Add id for edit/delete
        }
        for recipe in recipes
    ]
    return jsonify(recipes_data)

@recipe_bp.route('/usage', methods=['GET'])
def usage():
    from database import db
    from models import Production, RecipeMaster
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
    return render_template('recipe/usage.html', usage_data=usage_data)

@recipe_bp.route('/raw_material_report', methods=['GET'])
def raw_material_report():
    from database import db
    from models import Production, RecipeMaster
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
    raw_material_totals = {}
    for entry in usage_data:
        raw_material = entry['raw_material']
        usage = entry['usage']
        if raw_material in raw_material_totals:
            raw_material_totals[raw_material] += usage
        else:
            raw_material_totals[raw_material] = usage
    raw_material_data = [
        {'raw_material': material, 'meat_required': round(total, 2)}
        for material, total in raw_material_totals.items()
    ]
    raw_material_data.sort(key=lambda x: x['raw_material'])
    return render_template('recipe/raw_material.html', raw_material_data=raw_material_data)