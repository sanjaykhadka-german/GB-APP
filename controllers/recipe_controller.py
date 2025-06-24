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
# from models.joining import Joining  # REMOVED - joining table deprecated
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
            
            # Check for duplicate (recipe_code, assembly_item_id, component_item_id) in the same submission
            seen = set()
            for recipe_data in recipes_data:
                key = (recipe_data.get('recipe_code'), recipe_data.get('assembly_item_id'), recipe_data.get('component_item_id'))
                if key in seen:
                    return jsonify({'error': f"Duplicate entry for recipe code {key[0]} with the same assembly and component in the same submission."}), 400
                seen.add(key)

                recipe_id = recipe_data.get('recipe_id')
                recipe_code = recipe_data.get('recipe_code')
                description = recipe_data.get('description')
                finished_good_id = recipe_data.get('finished_good_id')
                raw_material_id = recipe_data.get('raw_material_id')
                kg_per_batch = recipe_data.get('kg_per_batch')

                if not all([recipe_code, description, finished_good_id, raw_material_id, kg_per_batch]):
                    return jsonify({'error': 'Required fields are missing.'}), 400
                
                # Validate kg_per_batch is a number
                try:
                    kg_per_batch = Decimal(kg_per_batch)
                    if kg_per_batch <= 0:
                        return jsonify({'error': 'Kg per batch cannot be negative or zero.'}), 400
                except (ValueError, TypeError):
                    return jsonify({'error': 'Invalid kg per batch value.'}), 400

                # Check if a recipe with the same (finished_good_id, raw_material_id) exists (excluding current recipe if editing)
                existing_recipe = RecipeMaster.query.filter(
                    RecipeMaster.finished_good_id == finished_good_id,
                    RecipeMaster.raw_material_id == raw_material_id,
                    RecipeMaster.id != recipe_id if recipe_id else True
                ).first()
                if existing_recipe:
                    return jsonify({'error': f"Recipe for this finished good-raw material combination already exists."}), 400

            # Process all recipes
            for recipe_data in recipes_data:
                recipe_id = recipe_data.get('recipe_id')
                recipe_code = recipe_data.get('recipe_code')
                description = recipe_data.get('description')
                finished_good_id = recipe_data.get('finished_good_id')
                raw_material_id = recipe_data.get('raw_material_id')
                kg_per_batch = Decimal(recipe_data.get('kg_per_batch'))

                if recipe_id:  # Edit case
                    recipe = RecipeMaster.query.get_or_404(recipe_id)
                    recipe.recipe_code = recipe_code
                    recipe.description = description
                    recipe.finished_good_id = finished_good_id
                    recipe.raw_material_id = raw_material_id
                    recipe.kg_per_batch = kg_per_batch
                else:  # Add case
                    recipe = RecipeMaster(
                        recipe_code=recipe_code,
                        description=description,
                        finished_good_id=finished_good_id,
                        raw_material_id=raw_material_id,
                        kg_per_batch=kg_per_batch
                    )
                    db.session.add(recipe)

                db.session.flush()

            # Recalculate percentages for all recipes with the same recipe_code
            recipe_code = recipes_data[0]['recipe_code']
            recipes_to_update = RecipeMaster.query.filter(
                RecipeMaster.recipe_code == recipe_code
            ).all()

            total_quantity = sum(float(r.kg_per_batch) for r in recipes_to_update)
            for r in recipes_to_update:
                r.percentage = Decimal(round((float(r.kg_per_batch) / total_quantity) * 100, 2)) if total_quantity > 0 else Decimal('0.00')

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
    
    # Get all items for dropdowns (any item can be used as component or assembly)
    all_items = ItemMaster.query.order_by(ItemMaster.item_code).all()

    return render_template('recipe/recipe.html', 
                         search_recipe_code=search_recipe_code,
                         search_description=search_description,
                         recipes=RecipeMaster.query.all(),
                         all_items=all_items,
                         current_page='recipe')

@recipe_bp.route('/recipe/delete/<int:id>', methods=['POST'])
def delete_recipe(id):
    try:
        recipe = RecipeMaster.query.get_or_404(id)
        recipe_code = recipe.recipe_code
        db.session.delete(recipe)
        db.session.commit()

        # Recalculate percentages for remaining recipes with the same recipe_code
        recipes_to_update = RecipeMaster.query.filter(RecipeMaster.recipe_code == recipe_code).all()
        if recipes_to_update:
            total_quantity = sum(float(r.kg_per_batch) for r in recipes_to_update)
            for r in recipes_to_update:
                r.percentage = Decimal(round((float(r.kg_per_batch) / total_quantity) * 100, 2)) if total_quantity > 0 else Decimal('0.00')
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
    
    # Create aliases for the two ItemMaster joins
    from sqlalchemy.orm import aliased
    RawMaterialItem = aliased(ItemMaster)
    FinishedGoodItem = aliased(ItemMaster)
    
    # Join with both raw material and finished good items
    recipes_query = db.session.query(
        RecipeMaster,
        RawMaterialItem.item_code.label('raw_material_code'),
        RawMaterialItem.description.label('raw_material'),
        FinishedGoodItem.item_code.label('finished_good_code'),
        FinishedGoodItem.description.label('finished_good')
    ).join(
        RawMaterialItem,
        RecipeMaster.raw_material_id == RawMaterialItem.id
    ).join(
        FinishedGoodItem,
        RecipeMaster.finished_good_id == FinishedGoodItem.id
    )
    
    if search_recipe_code:
        recipes_query = recipes_query.filter(RecipeMaster.recipe_code.ilike(f"%{search_recipe_code}%"))
    if search_description:
        recipes_query = recipes_query.filter(RecipeMaster.description.ilike(f"%{search_description}%"))
    
    recipes = recipes_query.all()
    
    recipes_data = []
    for recipe in recipes:
        recipes_data.append({
            "id": recipe.RecipeMaster.id,
            "recipe_code": recipe.RecipeMaster.recipe_code,
            "description": recipe.RecipeMaster.description,
            "raw_material_code": recipe.raw_material_code,
            "raw_material": recipe.raw_material,
            "raw_material_id": recipe.RecipeMaster.raw_material_id,
            "finished_good_code": recipe.finished_good_code,
            "finished_good": recipe.finished_good,
            "finished_good_id": recipe.RecipeMaster.finished_good_id,
            "kg_per_batch": float(recipe.RecipeMaster.kg_per_batch) if recipe.RecipeMaster.kg_per_batch else 0.00,
            "percentage": float(recipe.RecipeMaster.percentage) if recipe.RecipeMaster.percentage else 0.00,
            "quantity_uom_id": recipe.RecipeMaster.quantity_uom_id
        })
    
    return jsonify(recipes_data)

@recipe_bp.route('/usage')
def usage():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    # Query to get production and recipe usage data
    query = db.session.query(
        Production,
        RecipeMaster,
        ItemMaster.description.label('component_name')
    ).join(
        RecipeMaster,
        Production.production_code == RecipeMaster.recipe_code  # Join Production to RecipeMaster
    ).join(
        ItemMaster,
        RecipeMaster.raw_material_id == ItemMaster.id  # Join RecipeMaster to ItemMaster for raw material
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
    for production, recipe, component_name in usage_data:
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
            'component_material': component_name,
            'usage_kg': recipe.kg_per_batch * production.batches,  # Scale by batches
            'kg_per_batch': recipe.kg_per_batch,
            'percentage': recipe.percentage if recipe.percentage else 0.0
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
        ItemMaster.description.label('component_name')
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
    for recipe, component_name in usage_data:
        # Calculate the Monday of the week for the created_at date
        week_commencing = get_monday_date(recipe.created_at.date().strftime('%Y-%m-%d'))
        data.append({
            'Week Commencing': week_commencing.strftime('%Y-%m-%d'),
            'Production Date': recipe.created_at.strftime('%Y-%m-%d'),
            'Recipe Code': recipe.recipe_code,
            'Component Material': component_name,
            'Kg per Batch': recipe.kg_per_batch
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
        
        # Base query for weekly data - using current schema
        raw_material_query = """
        SELECT 
            DATE(p.production_date - INTERVAL (WEEKDAY(p.production_date)) DAY) as week_commencing,
            im.description as component_material,
            im.id as component_item_id,
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
                raw_material=result.component_material,
                raw_material_id=result.component_item_id,
                meat_required=float(result.total_usage),
                created_at=datetime.now()
            )
            db.session.add(report)
        
        db.session.commit()
        
        # Convert to list of dictionaries for template
        raw_material_data = [
            {
                'week_commencing': result.week_commencing.strftime('%d/%m/%Y'),
                'raw_material': result.component_material,
                'usage': round(float(result.total_usage), 2)
            }
            for result in results
        ]
        
        return render_template('recipe/raw_material_report.html', 
                             raw_material_data=raw_material_data,
                             week_commencing=week_commencing,
                             current_page='raw_material_report')
        
    except Exception as e:
        flash(f"An error occurred: {str(e)}", 'error')
        return render_template('recipe/raw_material_report.html', 
                             raw_material_data=[],
                             week_commencing=week_commencing,
                             current_page='raw_material_report')

@recipe_bp.route('/raw_material_download', methods=['GET'])
def raw_material_download():
    try:
        week_commencing = request.args.get('week_commencing')
        
        # Base query for weekly data - using current schema
        raw_material_query = """
        SELECT 
            DATE(p.production_date - INTERVAL (WEEKDAY(p.production_date)) DAY) as week_commencing,
            im.description as component_material,
            im.id as component_item_id,
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
        
        # Convert to list of dictionaries for Excel
        data = [
            {
                'Week Commencing': result.week_commencing.strftime('%d/%m/%Y'),
                'Component Material': result.component_material,
                'Total Usage (kg)': round(float(result.total_usage), 2)
            }
            for result in results
        ]
        
        if not data:
            flash("No data available for the selected week.", 'warning')
            return redirect(url_for('recipe.raw_material_report'))
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Create Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Raw Material Report', index=False)
            
            # Get the workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets['Raw Material Report']
            
            # Add formatting
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BC',
                'border': 1
            })
            
            # Write the column headers with the defined format
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Adjust column widths
            worksheet.set_column('A:A', 15)  # Week Commencing
            worksheet.set_column('B:B', 30)  # Component Material
            worksheet.set_column('C:C', 15)  # Total Usage
        
        output.seek(0)
        
        filename = f'raw_material_report_{week_commencing}.xlsx' if week_commencing else 'raw_material_report.xlsx'
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f"Error generating Excel file: {str(e)}", 'error')
        return redirect(url_for('recipe.raw_material_report')) 