from flask import Blueprint, render_template, request, redirect, send_file, url_for, flash, jsonify
from sqlalchemy.sql import text
from decimal import Decimal
import sqlalchemy.exc
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO
from database import db
from models import Production, RecipeMaster, UsageReport, RawMaterialReport, ItemMaster
from models.usage_report import UsageReport
from models.recipe_master import RecipeMaster
from models.production import Production
from models.joining import Joining
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment


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
    monday = date - timedelta(days=days_since_monday)
    return monday

@recipe_bp.route('/recipe', methods=['GET', 'POST'])
def recipe_page():
    if request.method == 'POST':
        try:
            data = request.get_json() 
            recipes_data = data.get('recipes', [])

            if not recipes_data:
                return jsonify({'error': 'No recipes data provided.'}), 400
            
            # Validate description are unique
            descriptions = {recipe.get('description') for recipe in recipes_data}
            if len(descriptions) > 1:
                return jsonify({'error': 'All recipes must have the same description.'}), 400
            
            # Check for duplicate (recipe_code, raw_material_id, finished_good_id) in the same submission
            seen = set()
            for recipe_data in recipes_data:
                key = (recipe_data.get('recipe_code'), recipe_data.get('raw_material_id'), recipe_data.get('finished_good_id'))
                if key in seen:
                    return jsonify({'error': f"Duplicate entry for recipe code {key[0]} with the same raw material and finished good in the same submission."}), 400
                seen.add(key)

                recipe_id = recipe_data.get('recipe_id')
                recipe_code = recipe_data.get('recipe_code')
                description = recipe_data.get('description')
                raw_material_id = recipe_data.get('raw_material_id')
                finished_good_id = recipe_data.get('finished_good_id')
                kg_per_batch = recipe_data.get('kg_per_batch')

                if not all([recipe_code, description, raw_material_id, finished_good_id, kg_per_batch]):
                    return jsonify({'error': 'Required fields are missing.'}), 400
                
                # Validate kg_per_batch is a number
                try:
                    kg_per_batch = Decimal(kg_per_batch)
                    if kg_per_batch <= 0:
                        return jsonify({'error': 'KG per batch cannot be negative.'}), 400
                except (ValueError, TypeError):
                    return jsonify({'error': 'Invalid KG per batch value.'}), 400

                # Check if a recipe with the same (recipe_code, raw_material_id, finished_good_id) exists (excluding current recipe if editing)
                existing_recipe = RecipeMaster.query.filter(
                    RecipeMaster.recipe_code == recipe_code,
                    RecipeMaster.raw_material_id == raw_material_id,
                    RecipeMaster.finished_good_id == finished_good_id,
                    RecipeMaster.id != recipe_id if recipe_id else True
                ).first()
                if existing_recipe:
                    return jsonify({'error': f"Recipe with code {recipe_code}, raw material, and finished good already exists."}), 400

            # Process all recipes
            for recipe_data in recipes_data:
                recipe_id = recipe_data.get('recipe_id')
                recipe_code = recipe_data.get('recipe_code')
                description = recipe_data.get('description')
                raw_material_id = recipe_data.get('raw_material_id')
                finished_good_id = recipe_data.get('finished_good_id')
                kg_per_batch = Decimal(recipe_data.get('kg_per_batch'))

                if recipe_id:  # Edit case
                    recipe = RecipeMaster.query.get_or_404(recipe_id)
                    recipe.recipe_code = recipe_code
                    recipe.description = description
                    recipe.raw_material_id = raw_material_id
                    recipe.finished_good_id = finished_good_id
                    recipe.kg_per_batch = kg_per_batch
                else:  # Add case
                    recipe = RecipeMaster(
                        recipe_code=recipe_code,
                        description=description,
                        raw_material_id=raw_material_id,
                        finished_good_id=finished_good_id,
                        kg_per_batch=kg_per_batch,
                        percentage=Decimal('0.00')
                    )
                    db.session.add(recipe)

                db.session.flush()

            # Recalculate percentages for all recipes with the same description
            description = recipes_data[0]['description']
            recipes_to_update = RecipeMaster.query.filter(
                RecipeMaster.description == description
                ).all()

            total_kg = sum(float(r.kg_per_batch) for r in recipes_to_update)
            for r in recipes_to_update:
                r.percentage = Decimal(round((float(r.kg_per_batch) / total_kg) * 100, 2)) if total_kg > 0 else Decimal('0.00')
            
            db.session.commit()
            return jsonify({'message': 'Recipes saved successfully!'}), 200

        except sqlalchemy.exc.IntegrityError as e:
            db.session.rollback()
            return jsonify({'error': 'Database error: Duplicate entry or invalid data.'}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'An error occurred: {str(e)}'}), 500

    # GET request: render the page
    search_recipe_code = request.args.get('recipe_code', '')
    search_description = request.args.get('description', '')
    edit_id = request.args.get('edit_id')
    
    # Get all raw materials and finished goods for the dropdowns
    raw_materials = ItemMaster.query.filter(ItemMaster.item_type == 'Raw Material').order_by(ItemMaster.item_code).all()
    finished_goods = ItemMaster.query.filter(ItemMaster.item_type == 'Finished Good').order_by(ItemMaster.item_code).all()

    
    return render_template('recipe/recipe.html', 
                         search_recipe_code=search_recipe_code,
                         search_description=search_description,
                         recipes=RecipeMaster.query.all(),
                         raw_materials=raw_materials,
                         finished_goods=finished_goods,
                         current_page='recipe')

@recipe_bp.route('/recipe/delete/<int:id>', methods=['POST'])
def delete_recipe(id):
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
                r.percentage = Decimal(round((float(r.kg_per_batch) / total_kg) * 100, 2)) if total_kg > 0 else Decimal('0.00')
            db.session.commit()

        return jsonify({'message': 'Recipe deleted successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@recipe_bp.route('/autocomplete_recipe', methods=['GET'])
def autocomplete_recipe():
  
    search = request.args.get('query', '').strip()
    if not search:
        return jsonify([])
    try:
        query = text("SELECT recipe_code, description FROM recipe_master WHERE recipe_code LIKE :search LIMIT 10")
        results = db.session.execute(query, {"search": f"{search}%"}).fetchall()
        suggestions = [{"recipe_code": row[0], "description": row[1]} for row in results]
        return jsonify(suggestions)
    except Exception as e:
        print(f"Error fetching recipe autocomplete suggestions: {e}")
        return jsonify([])

@recipe_bp.route('/get_search_recipes', methods=['GET'])
def get_search_recipes():
    search_recipe_code = request.args.get('recipe_code', '').strip()
    search_description = request.args.get('description', '').strip()
    
    # Join with item_master to get the raw material code and name
    recipes_query = db.session.query(
        RecipeMaster,
        ItemMaster.item_code.label('raw_material_code'),  # Add item_code
        ItemMaster.description.label('raw_material_name')
    ).join(
        ItemMaster,
        RecipeMaster.raw_material_id == ItemMaster.id
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
            "raw_material_code": recipe.raw_material_code,  # Add raw_material_code
            "raw_material": recipe.raw_material_name,
            "raw_material_id": recipe.RecipeMaster.raw_material_id,
            "finished_good_id": recipe.RecipeMaster.finished_good_id,
            "kg_per_batch": float(recipe.RecipeMaster.kg_per_batch) if recipe.RecipeMaster.kg_per_batch else 0.00,
            "percentage": round(float(recipe.RecipeMaster.percentage), 2) if recipe.RecipeMaster.percentage else 0.00
        }
        for recipe in recipes
    ]
    
    return jsonify(recipes_data)

@recipe_bp.route('/usage')
def usage():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    # Query to get production and recipe usage data
    query = db.session.query(
        Production,
        RecipeMaster,
        ItemMaster.description.label('raw_material_name')
    ).join(
        RecipeMaster,
        Production.production_code == RecipeMaster.recipe_code  # Join Production to RecipeMaster
    ).join(
        ItemMaster,
        RecipeMaster.raw_material_id == ItemMaster.id  # Join RecipeMaster to ItemMaster
    )
    
    # Apply date filters if provided
    if from_date and to_date:
        query = query.filter(
            Production.production_date >= from_date,
            Production.production_date <= to_date
        )
    
    # Get the results
    usage_data = query.all()
    
    # Group data by production date
    grouped_usage_data = {}
    for production, recipe, raw_material_name in usage_data:
        date = production.production_date  # production_date is already a date object
        # Calculate the Monday of the week for the production_date
        week_commencing = get_monday_date(date.strftime('%Y-%m-%d'))
        
        if date not in grouped_usage_data:
            grouped_usage_data[date] = []
            
        grouped_usage_data[date].append({
            'week_commencing': week_commencing.strftime('%Y-%m-%d'),
            'production_date': production.production_date.strftime('%Y-%m-%d'),
            'production_code': production.production_code,
            'recipe_code': recipe.recipe_code,
            'raw_material': raw_material_name,
            'usage_kg': recipe.kg_per_batch * production.batches,  # Scale by batches
            'percentage': recipe.percentage
        })
    
    return render_template('recipe/usage.html',
                         grouped_usage_data=grouped_usage_data,
                         from_date=from_date,
                         to_date=to_date,
                         current_page='usage')

@recipe_bp.route('/usage/download')
def usage_download():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    # Query to get usage data
    query = db.session.query(
        RecipeMaster,
        ItemMaster.description.label('raw_material_name')
    ).join(
        ItemMaster,
        RecipeMaster.raw_material_id == ItemMaster.id
    )
    
    # Apply date filters if provided
    if from_date and to_date:
        query = query.filter(
            RecipeMaster.created_at >= from_date,
            RecipeMaster.created_at <= to_date
        )
    
    # Get the results
    usage_data = query.all()
    
    # Create Excel file
    data = []
    for recipe, raw_material_name in usage_data:
        # Calculate the Monday of the week for the created_at date
        week_commencing = get_monday_date(recipe.created_at.date().strftime('%Y-%m-%d'))
        data.append({
            'Week Commencing': week_commencing.strftime('%Y-%m-%d'),
            'Production Date': recipe.created_at.strftime('%Y-%m-%d'),
            'Recipe Code': recipe.recipe_code,
            'Raw Material': raw_material_name,
            'Usage (kg)': recipe.kg_per_batch,
            'Percentage (%)': recipe.percentage
        })
    
    df = pd.DataFrame(data)
    
    # Create Excel file
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Usage Report', index=False)
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'usage_report_{from_date}_{to_date}.xlsx' if from_date and to_date else 'usage_report.xlsx'
    )   

@recipe_bp.route('/raw_material_report', methods=['GET'])
def raw_material_report():
    try:
        # Get week commencing filter from request
        week_commencing = request.args.get('week_commencing')
        
        # Base query for weekly data
        raw_material_query = """
        SELECT 
            DATE(p.production_date - INTERVAL (WEEKDAY(p.production_date)) DAY) as week_commencing,
            im.description as raw_material,
            im.id as raw_material_id,
            SUM(p.total_kg * r.percentage / 100) as total_usage
        FROM production p
        JOIN recipe_master r ON p.production_code = r.recipe_code
        JOIN item_master im ON r.raw_material_id = im.id
        """
        
        # Add date filter to the query
        params = {}
        if week_commencing:
            raw_material_query += """ 
            WHERE DATE(p.production_date - INTERVAL (WEEKDAY(p.production_date)) DAY) = :week_commencing
            """
            params['week_commencing'] = datetime.strptime(week_commencing, '%Y-%m-%d').date()
        
        raw_material_query += """
        GROUP BY 
            DATE(p.production_date - INTERVAL (WEEKDAY(p.production_date)) DAY),
            im.description,
            im.id
        ORDER BY week_commencing DESC, im.description
        """
        
        results = db.session.execute(text(raw_material_query), params).fetchall()
        
        # Clear existing records for the week
        if week_commencing:
            delete_query = "DELETE FROM raw_material_report WHERE week_commencing = :week_commencing"
            delete_params = {'week_commencing': datetime.strptime(week_commencing, '%Y-%m-%d').date()}
            db.session.execute(text(delete_query), delete_params)
        
        # Save results to raw_material_report table
        for result in results:
            report = RawMaterialReport(
                production_date=result.week_commencing,  # Using week_commencing as production_date
                week_commencing=result.week_commencing,
                raw_material=result.raw_material,
                raw_material_id=result.raw_material_id,
                meat_required=float(result.total_usage),
                created_at=datetime.now()
            )
            db.session.add(report)
        
        db.session.commit()
        
        # Convert to list of dictionaries for template
        raw_material_data = [
            {
                'week_commencing': result.week_commencing.strftime('%d/%m/%Y'),
                'raw_material': result.raw_material,
                'usage': round(float(result.total_usage), 2)
            }
            for result in results
        ]
        
        return render_template('recipe/raw_material_report.html', 
                             raw_material_data=raw_material_data,
                             current_page='raw_material_report')
    
    except Exception as e:
        db.session.rollback()
        flash(f"Error generating raw material report: {str(e)}", 'error')
        return render_template('recipe/raw_material_report.html', 
                             raw_material_data=[],
                             current_page='raw_material_report')

@recipe_bp.route('/raw_material_download', methods=['GET'])
def raw_material_download():
    try:
        # Get week commencing filter from request
        week_commencing = request.args.get('week_commencing')
        
        # Base query for weekly data
        raw_material_query = """
        SELECT 
            DATE(p.production_date - INTERVAL (WEEKDAY(p.production_date)) DAY) as week_commencing,
            im.description as raw_material,
            im.id as raw_material_id,
            SUM(p.total_kg * r.percentage / 100) as total_usage
        FROM production p
        JOIN recipe_master r ON p.production_code = r.recipe_code
        JOIN item_master im ON r.raw_material_id = im.id
        """
        
        # Add date filter to the query
        params = {}
        if week_commencing:
            raw_material_query += """ 
            WHERE DATE(p.production_date - INTERVAL (WEEKDAY(p.production_date)) DAY) = :week_commencing
            """
            params['week_commencing'] = datetime.strptime(week_commencing, '%Y-%m-%d').date()
        
        raw_material_query += """
        GROUP BY 
            DATE(p.production_date - INTERVAL (WEEKDAY(p.production_date)) DAY),
            im.description,
            im.id
        ORDER BY week_commencing DESC, im.description
        """
        
        results = db.session.execute(text(raw_material_query), params).fetchall()
        
        # Create Excel workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Raw Material Report"
        
        # Define headers
        headers = [
            "Week Commencing",
            "Raw Material",
            "Usage (kg)"
        ]
        ws.append(headers)
        
        # Style headers
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
        
        # Populate data
        for result in results:
            ws.append([
                result.week_commencing.strftime('%d/%m/%Y'),
                result.raw_material,
                round(float(result.total_usage), 2)
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
    except Exception as e:
        print(f"Error in raw_material_download: {str(e)}")
        flash(f"Error downloading report: {str(e)}", 'error')
        return redirect(url_for('recipe.raw_material_report'))