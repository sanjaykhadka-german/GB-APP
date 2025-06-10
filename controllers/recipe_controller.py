from flask import Blueprint, render_template, request, redirect, send_file, url_for, flash, jsonify
from sqlalchemy.sql import text
from decimal import Decimal
import sqlalchemy.exc
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO
from database import db
from models import Production, RecipeMaster, RawMaterials, UsageReport, RawMaterialReport
from models.usage_report import UsageReport
from models.recipe_master import RecipeMaster
from models.raw_materials import RawMaterials
from models.production import Production


# Create a Blueprint for recipe routes
recipe_bp = Blueprint('recipe', __name__, template_folder='templates')

def get_monday_date(date_str):
    """Convert any date to the previous Monday if it's not already a Monday.
    Supports both YYYY-MM-DD and DD/MM/YYYY formats."""
    try:
        # Try YYYY-MM-DD format first
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        try:
            # Try DD/MM/YYYY format
            date = datetime.strptime(date_str, '%d/%m/%Y').date()
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD or DD/MM/YYYY format")
    
    days_since_monday = date.weekday()  # Monday = 0, Sunday = 6
    if days_since_monday != 0:  # If not Monday
        # Calculate previous Monday
        monday = date - timedelta(days=days_since_monday)
        return monday
    return date

@recipe_bp.route('/recipe', methods=['GET', 'POST'])
def recipe_page():
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form
            recipes_data = data.get('recipes', [])
            
            for recipe_data in recipes_data:
                recipe_id = recipe_data.get('recipe_id')
                recipe_code = recipe_data.get('recipe_code')
                description = recipe_data.get('description')
                raw_material_id = recipe_data.get('raw_material_id')
                kg_per_batch = recipe_data.get('kg_per_batch')

                if not all([recipe_code, description, raw_material_id, kg_per_batch]):
                    return jsonify({'error': 'Required fields are missing.'}), 400

                kg_per_batch = Decimal(kg_per_batch)

                # Get current date and calculate its Monday (week commencing)
                today = datetime.now().date()
                week_commencing = today - timedelta(days=today.weekday())

                if recipe_id:  # Edit case
                    recipe = RecipeMaster.query.get_or_404(recipe_id)
                    recipe.recipe_code = recipe_code
                    recipe.description = description
                    recipe.raw_material_id = raw_material_id
                    recipe.kg_per_batch = kg_per_batch
                else:  # Add case
                    recipe = RecipeMaster(
                        recipe_code=recipe_code,
                        description=description,
                        raw_material_id=raw_material_id,
                        kg_per_batch=kg_per_batch,
                        percentage=Decimal(0),
                        week_commencing=week_commencing  # Add week commencing date
                    )
                    db.session.add(recipe)

                db.session.flush()

            # Recalculate percentages for all recipes with the same description
            for recipe_data in recipes_data:
                recipes_to_update = RecipeMaster.query.filter(
                    RecipeMaster.description == recipe_data['description']
                ).all()
                
                total_kg = sum(float(r.kg_per_batch) for r in recipes_to_update)
                for r in recipes_to_update:
                    r.percentage = Decimal((float(r.kg_per_batch) / total_kg) * 100) if total_kg > 0 else Decimal(0)
            
            db.session.commit()
            return jsonify({'message': 'Recipes saved successfully!'}), 200

        except ValueError as e:
            db.session.rollback()
            return jsonify({'error': f'Invalid input: {str(e)}'}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'An error occurred: {str(e)}'}), 500

    # GET request: render the page
    search_recipe_code = request.args.get('recipe_code', '')
    search_description = request.args.get('description', '')
    edit_id = request.args.get('edit_id')
    
    # Get all raw materials for the dropdowns
    raw_materials = RawMaterials.query.order_by(RawMaterials.raw_material).all()
    
    if edit_id:
        recipe = RecipeMaster.query.get_or_404(edit_id)
        return render_template('recipe/recipe.html', 
                             search_recipe_code=search_recipe_code,
                             search_description=search_description,
                             recipes=RecipeMaster.query.all(),
                             raw_materials=raw_materials,
                             edit_recipe=recipe,
                             current_page='recipe')
    
    return render_template('recipe/recipe.html', 
                         search_recipe_code=search_recipe_code,
                         search_description=search_description,
                         recipes=RecipeMaster.query.all(),
                         raw_materials=raw_materials,
                         current_page='recipe')

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
    search_recipe_code = request.args.get('recipe_code', '').strip()
    search_description = request.args.get('description', '').strip()
    
    # Join with raw_materials to get the raw material name
    recipes_query = db.session.query(
        RecipeMaster, 
        RawMaterials.raw_material
    ).join(
        RawMaterials, 
        RecipeMaster.raw_material_id == RawMaterials.id
    )
    
    if search_recipe_code:
        recipes_query = recipes_query.filter(RecipeMaster.recipe_code.ilike(f"%{search_recipe_code}%"))
    if search_description:
        recipes_query = recipes_query.filter(RecipeMaster.description.ilike(f"%{search_description}%"))
    
    recipes = recipes_query.all()
    recipes_data = [
        {
            "id": recipe.RecipeMaster.id,
            "recipe_code": recipe.RecipeMaster.recipe_code,
            "description": recipe.RecipeMaster.description,
            "raw_material": recipe.raw_material,
            "raw_material_id": recipe.RecipeMaster.raw_material_id,
            "kg_per_batch": float(recipe.RecipeMaster.kg_per_batch),
            "percentage": float(recipe.RecipeMaster.percentage) if recipe.RecipeMaster.percentage else 0.0
        }
        for recipe in recipes
    ]
    return jsonify(recipes_data)

@recipe_bp.route('/usage', methods=['GET'])
def usage():
    try:
        print("\nStarting usage report generation...")  # Debug log
        
        # Get date filters from request
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        
        # Base query
        query = UsageReport.query.order_by(UsageReport.production_date.desc())
        
        # Apply date filters if provided
        if from_date:
            query = query.filter(UsageReport.production_date >= datetime.strptime(from_date, '%Y-%m-%d').date())
        if to_date:
            query = query.filter(UsageReport.production_date <= datetime.strptime(to_date, '%Y-%m-%d').date())
        
        # Get the filtered data
        usage_records = query.all()
        print(f"Found {len(usage_records)} records in usage_report table")  # Debug log
        
        # Group usage data by production_date for display
        grouped_usage_data = {}
        for record in usage_records:
            date_str = record.production_date.strftime('%d/%m/%Y')
            if date_str not in grouped_usage_data:
                grouped_usage_data[date_str] = []
                print(f"Processing date: {date_str}")  # Debug log
                
            grouped_usage_data[date_str].append({
                'production_date': date_str,
                'recipe_code': record.recipe_code,
                'raw_material': record.raw_material,
                'usage_kg': round(float(record.usage_kg), 2),
                'percentage': round(float(record.percentage), 2)
            })
        
        print(f"Grouped data by {len(grouped_usage_data)} dates")  # Debug log
        
        # Sort dates in reverse chronological order
        sorted_usage_data = dict(sorted(grouped_usage_data.items(), 
                                      key=lambda x: datetime.strptime(x[0], '%d/%m/%Y'),
                                      reverse=True))
        
        print("Rendering template with data...")  # Debug log
        print(f"Sample data for first date: {list(sorted_usage_data.values())[0] if sorted_usage_data else []}")  # Debug log
        
        return render_template('recipe/usage.html', 
                             grouped_usage_data=sorted_usage_data, 
                             current_page='usage')
    
    except Exception as e:
        print(f"Error in usage function: {str(e)}")  # Debug log
        import traceback
        print(f"Traceback: {traceback.format_exc()}")  # Debug log
        db.session.rollback()
        flash(f"Error generating usage report: {str(e)}", 'error')
        return render_template('recipe/usage.html', 
                             grouped_usage_data={}, 
                             current_page='usage')

@recipe_bp.route('/usage_download', methods=['GET'])
def usage_download():
    from database import db
    from models import UsageReport
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment
    from io import BytesIO
    from flask import send_file
    from datetime import datetime
    
    # Get date filters from request
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    # Base query
    query = UsageReport.query
    
    # Apply date filters if provided
    if from_date:
        query = query.filter(UsageReport.production_date >= datetime.strptime(from_date, '%Y-%m-%d').date())
    if to_date:
        query = query.filter(UsageReport.production_date <= datetime.strptime(to_date, '%Y-%m-%d').date())
    
    # Get filtered records
    usage_records = query.order_by(UsageReport.production_date.desc()).all()
    
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
    try:
        # Get date filters from request
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        
        # Base query
        raw_material_query = """
        SELECT 
            p.production_date,
            rm.raw_material,
            SUM(p.total_kg * r.percentage / 100) as total_usage
        FROM production p
        JOIN recipe_master r ON p.production_code = r.recipe_code
        JOIN raw_materials rm ON r.raw_material_id = rm.id
        """
        
        # Add date filters to the query
        conditions = []
        params = {}
        
        if from_date:
            conditions.append("p.production_date >= :from_date")
            params['from_date'] = datetime.strptime(from_date, '%Y-%m-%d').date()
        
        if to_date:
            conditions.append("p.production_date <= :to_date")
            params['to_date'] = datetime.strptime(to_date, '%Y-%m-%d').date()
        
        if conditions:
            raw_material_query += " WHERE " + " AND ".join(conditions)
        
        raw_material_query += """
        GROUP BY p.production_date, rm.raw_material
        ORDER BY p.production_date DESC, rm.raw_material
        """
        
        results = db.session.execute(text(raw_material_query), params).fetchall()
        
        # Convert to list of dictionaries for template
        raw_material_data = [
            {
                'production_date': result.production_date.strftime('%d/%m/%Y'),
                'raw_material': result.raw_material,
                'usage': round(float(result.total_usage), 2)
            }
            for result in results
        ]
        
        return render_template('recipe/raw_material_report.html', 
                             raw_material_data=raw_material_data,
                             current_page='raw_material_report')
    
    except Exception as e:
        flash(f"Error generating raw material report: {str(e)}", 'error')
        return render_template('recipe/raw_material_report.html', 
                             raw_material_data=[],
                             current_page='raw_material_report')

@recipe_bp.route('/raw_material_download', methods=['GET'])
def raw_material_download():
    from database import db
    from models import UsageReport
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment
    from io import BytesIO
    from flask import send_file
    from datetime import datetime

    # Get date filters from request
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    # Base query
    query = UsageReport.query
    
    # Apply date filters if provided
    if from_date:
        query = query.filter(UsageReport.production_date >= datetime.strptime(from_date, '%Y-%m-%d').date())
    if to_date:
        query = query.filter(UsageReport.production_date <= datetime.strptime(to_date, '%Y-%m-%d').date())
    
    # Get filtered records
    usage_records = query.order_by(UsageReport.production_date.desc()).all()

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
    ), reverse=True)

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