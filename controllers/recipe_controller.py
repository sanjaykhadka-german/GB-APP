from flask import Blueprint, render_template, request, redirect, send_file, url_for, flash, jsonify
from sqlalchemy.sql import text
from decimal import Decimal
import sqlalchemy.exc
from datetime import datetime
import pandas as pd
from io import BytesIO
from database import db
from models import Production, RecipeMaster


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
                                     recipes=RecipeMaster.query.all(), current_page='recipe')

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
                                 recipes=RecipeMaster.query.all(),current_page='recipe')

        except sqlalchemy.exc.IntegrityError as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", 'error')
            return render_template('recipe/recipe.html', 
                                 search_recipe_code=request.args.get('recipe_code', ''),
                                 search_description=request.args.get('description', ''),
                                 recipes=RecipeMaster.query.all(), current_page='recipe')

        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred: {str(e)}", 'error')
            return render_template('recipe/recipe.html', 
                                 search_recipe_code=request.args.get('recipe_code', ''),
                                 search_description=request.args.get('description', ''),
                                 recipes=RecipeMaster.query.all(), current_page='recipe')

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
                             edit_recipe=recipe, current_page='recipe')
    return render_template('recipe/recipe.html', 
                         search_recipe_code=search_recipe_code,
                         search_description=search_description,
                         recipes=RecipeMaster.query.all(), current_page='recipe')

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
    from models import Production, RecipeMaster, UsageReport
    from datetime import datetime
    
    # Check if usage data exists in the database
    usage_records = UsageReport.query.all()
    
    if not usage_records:
        # Fetch all productions
        productions = Production.query.all()
        
        for production in productions:
            recipes = RecipeMaster.query.filter_by(recipe_code=production.production_code).all()
            if not recipes:
                continue
            for recipe in recipes:
                usage_kg = float(production.total_kg) * (float(recipe.percentage) / 100)
                # Create usage record
                usage_record = UsageReport(
                    production_date=production.production_date,
                    week_commencing=production.week_commencing,
                    recipe_code=production.production_code,
                    raw_material=recipe.raw_material,
                    usage_kg=round(usage_kg, 2),
                    percentage=float(recipe.percentage)
                )
                db.session.add(usage_record)
        db.session.commit()
        usage_records = UsageReport.query.all()
    
    # Group usage data by production_date
    grouped_usage_data = {}
    for record in usage_records:
        date_str = record.production_date.strftime('%d/%m/%Y')
        if date_str not in grouped_usage_data:
            grouped_usage_data[date_str] = []
        grouped_usage_data[date_str].append({
            'recipe_code': record.recipe_code,
            'raw_material': record.raw_material,
            'usage_kg': record.usage_kg,
            'percentage': record.percentage,
            'week_commencing': record.week_commencing.strftime('%d/%m/%Y') if record.week_commencing else '',
            'production_date': date_str
        })
    
    # Sort dates
    sorted_usage_data = dict(sorted(grouped_usage_data.items(), key=lambda x: datetime.strptime(x[0], '%d/%m/%Y')))
    
    return render_template('recipe/usage.html', grouped_usage_data=sorted_usage_data, current_page='usage')


@recipe_bp.route('/usage_download', methods=['GET'])
def usage_download():
    from database import db
    from models import UsageReport
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment
    from io import BytesIO
    from flask import send_file
    from datetime import datetime
    
    # Fetch usage records
    usage_records = UsageReport.query.all()
    
    # Create Excel workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Usage Report"
    
    # Define headers
    headers = [
        "Week Commencing",
        "Production Date",
        "Recipe Code",
        "Raw Material",
        "Usage (kg)",
        "Percentage (%)"
    ]
    ws.append(headers)
    
    # Style headers
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')
    
    # Populate data
    for record in usage_records:
        ws.append([
            record.week_commencing.strftime('%d/%m/%Y') if record.week_commencing else '',
            record.production_date.strftime('%d/%m/%Y'),
            record.recipe_code,
            record.raw_material,
            record.usage_kg,
            record.percentage
        ])
    
    # Auto-adjust column widths
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2) * 1.2
        ws.column_dimensions[column].width = adjusted_width
    
    # Save to BytesIO
    excel_file = BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)
    
    return send_file(
        excel_file,
        download_name=f"usage_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )



@recipe_bp.route('/raw_material_report', methods=['GET'])
def raw_material_report():
    from database import db
    from models import Production, RecipeMaster

    productions = Production.query.all()
    usage_data = []

    # Collect all usage data
    for production in productions:
        recipes = RecipeMaster.query.filter_by(recipe_code=production.production_code).all()
        if not recipes:
            continue
        for recipe in recipes:
            usage = float(production.total_kg) * (float(recipe.percentage) / 100)
            usage_data.append({
                'week_commencing': production.week_commencing.strftime('%d/%m/%Y') if production.week_commencing else '',
                'production_date': production.production_date.strftime('%d/%m/%Y'),
                'raw_material': recipe.raw_material,
                'usage': round(usage, 2)
            })

    # Aggregate usage by week_commencing, production_date, and raw_material
    raw_material_totals = {}
    for entry in usage_data:
        key = (entry['week_commencing'], entry['production_date'], entry['raw_material'])
        if key in raw_material_totals:
            raw_material_totals[key] += entry['usage']
        else:
            raw_material_totals[key] = entry['usage']

    # Convert to list of dictionaries for template
    raw_material_data = [
        {
            'week_commencing': key[0],
            'production_date': key[1],
            'raw_material': key[2],
            'usage': round(total, 2)
        }
        for key, total in raw_material_totals.items()
    ]

    # Sort by week_commencing, production_date, and raw_material
    raw_material_data.sort(key=lambda x: (x['week_commencing'] or '', x['production_date'], x['raw_material']))

    return render_template('recipe/raw_material.html', raw_material_data=raw_material_data, current_page='raw_material')

@recipe_bp.route('/raw_material_download', methods=['GET'])
def raw_material_download():
    from database import db
    from models import Production, RecipeMaster
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment
    from io import BytesIO
    from flask import send_file
    from datetime import datetime

    # Fetch raw material data
    productions = Production.query.all()
    raw_material_data = []

    for production in productions:
        recipes = RecipeMaster.query.filter_by(recipe_code=production.production_code).all()
        if not recipes:
            continue
        for recipe in recipes:
            usage_kg = float(production.total_kg) * (float(recipe.percentage) / 100)
            raw_material_data.append({
                'week_commencing': production.week_commencing.strftime('%d/%m/%Y') if production.week_commencing else '',
                'production_date': production.production_date.strftime('%d/%m/%Y'),
                'raw_material': recipe.raw_material,
                'usage_kg': round(usage_kg, 2),
            })

    # Create Excel workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Raw Material Report"

    # Define headers
    headers = [
        "Week Commencing",
        "Production Date",
        "Raw Material",
        "Usage (kg)"
    ]
    ws.append(headers)

    # Style headers
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')

    # Populate data
    for entry in raw_material_data:
        ws.append([
            entry['week_commencing'],
            entry['production_date'],
            entry['raw_material'],
            entry['usage_kg']
        ])

    # Auto-adjust column widths
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2) * 1.2
        ws.column_dimensions[column].width = adjusted_width

    # Save to BytesIO
    excel_file = BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)

    return send_file(
        excel_file,
        download_name=f"raw_material_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )