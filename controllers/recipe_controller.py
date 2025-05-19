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

    db.session.execute(text('TRUNCATE TABLE usage_report'))
    db.session.commit()


    
    try:
        # Fetch all productions
        productions = Production.query.all()
        if not productions:
            print("No production records found.")
        
        for production in productions:
            recipes = RecipeMaster.query.filter_by(recipe_code=production.production_code).all()
            print(f"Processing production: {production.production_code}")
            print(f"Recipes found: {len(recipes)}")
            
            if not recipes:
                print(f"No recipes found for production code: {production.production_code}")
                continue
            
            for recipe in recipes:
                print(f"Processing recipe: {recipe.raw_material}")
                try:
                    # Calculate usage
                    if production.total_kg is None or recipe.percentage is None:
                        print(f"Invalid data: total_kg={production.total_kg}, percentage={recipe.percentage}")
                        continue
                    usage_kg = float(production.total_kg) * (float(recipe.percentage) / 100)
                    print(f"Calculated usage_kg: {usage_kg}")
                    
                    # Check if usage record already exists
                    existing_record = UsageReport.query.filter_by(
                        production_date=production.production_date,
                        recipe_code=production.production_code,
                        raw_material=recipe.raw_material
                    ).first()
                    
                    if existing_record:
                        # Update existing record
                        existing_record.usage_kg = round(usage_kg, 2)
                        existing_record.percentage = float(recipe.percentage)
                        print(f"Updated usage record for {recipe.raw_material}")
                    else:
                        # Create new usage record
                        usage_record = UsageReport(
                            production_date=production.production_date,
                            week_commencing=production.week_commencing,
                            recipe_code=production.production_code,
                            raw_material=recipe.raw_material,
                            usage_kg=round(usage_kg, 2),
                            percentage=float(recipe.percentage)
                        )
                        db.session.add(usage_record)
                        print(f"Added new usage record for {recipe.raw_material}")
                
                except Exception as e:
                    print(f"Error processing recipe {recipe.raw_material}: {str(e)}")
                    continue
        
        # Commit changes to the database
        db.session.commit()
        print("Database commit successful.")
    
    except Exception as e:
        db.session.rollback()
        print(f"Database commit failed: {str(e)}")
        # Optionally, return an error response
        return render_template('error.html', error=str(e)), 500
    
    # Fetch all usage records for display
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
    from models import UsageReport, RawMaterial
    from datetime import datetime

    # Fetch all usage records from UsageReport
    usage_records = UsageReport.query.all()

    # Aggregate usage by week_commencing, production_date, and raw_material
    raw_material_totals = {}
    for record in usage_records:
        week_commencing = record.week_commencing.strftime('%d/%m/%Y') if record.week_commencing else ''
        production_date = record.production_date.strftime('%d/%m/%Y')
        raw_material = record.raw_material
        usage_kg = record.usage_kg

        key = (week_commencing, production_date, raw_material)
        if key in raw_material_totals:
            raw_material_totals[key] += usage_kg
        else:
            raw_material_totals[key] = usage_kg

    # Save or update data in RawMaterial table
    try:
        for key, total in raw_material_totals.items():
            week_commencing, production_date, raw_material = key
            # Convert string dates back to datetime.date for database
            production_date_obj = datetime.strptime(production_date, '%d/%m/%Y').date()
            week_commencing_obj = datetime.strptime(week_commencing, '%d/%m/%Y').date() if week_commencing else None

            # Check if record    record already exists
            existing_record = RawMaterial.query.filter_by(
                production_date=production_date_obj,
                week_commencing=week_commencing_obj,
                raw_material=raw_material
            ).first()

            if existing_record:
                # Update existing record
                existing_record.meat_required = round(total, 2)
                print(f"Updated RawMaterial record for {raw_material} on {production_date}")
            else:
                # Create new record
                new_record = RawMaterial(
                    production_date=production_date_obj,
                    week_commencing=week_commencing_obj,
                    raw_material=raw_material,
                    meat_required=round(total, 2)
                )
                db.session.add(new_record)
                print(f"Added new RawMaterial record for {raw_material} on {production_date}")

        # Commit changes to the database
        db.session.commit()
        print("RawMaterial table updated successfully.")

    except Exception as e:
        db.session.rollback()
        print(f"Error saving to RawMaterial table: {str(e)}")
        # Optionally, handle the error (e.g., return an error page)
        return render_template('error.html', error=str(e)), 500

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
    raw_material_data.sort(key=lambda x: (
        x['week_commencing'] or '',
        datetime.strptime(x['production_date'], '%d/%m/%Y') if x['production_date'] else datetime.min,
        x['raw_material']
    ))

    return render_template('recipe/raw_material.html', raw_material_data=raw_material_data, current_page='raw_material')

@recipe_bp.route('/raw_material_download', methods=['GET'])
def raw_material_download():
    from database import db
    from models import UsageReport
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment
    from io import BytesIO
    from flask import send_file
    from datetime import datetime

    # Fetch all usage records from UsageReport
    usage_records = UsageReport.query.all()

    # Aggregate usage by week_commencing, production_date, and raw_material
    raw_material_totals = {}
    for record in usage_records:
        week_commencing = record.week_commencing.strftime('%d/%m/%Y') if record.week_commencing else ''
        production_date = record.production_date.strftime('%d/%m/%Y')
        raw_material = record.raw_material
        usage_kg = record.usage_kg

        key = (week_commencing, production_date, raw_material)
        if key in raw_material_totals:
            raw_material_totals[key] += usage_kg
        else:
            raw_material_totals[key] = usage_kg

    # Convert to list of dictionaries for Excel
    raw_material_data = [
        {
            'week_commencing': key[0],
            'production_date': key[1],
            'raw_material': key[2],
            'usage_kg': round(total, 2)
        }
        for key, total in raw_material_totals.items()
    ]

    # Sort by week_commencing, production_date, and raw_material
    raw_material_data.sort(key=lambda x: (
        x['week_commencing'] or '',
        datetime.strptime(x['production_date'], '%d/%m/%Y') if x['production_date'] else datetime.min,
        x['raw_material']
    ))

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