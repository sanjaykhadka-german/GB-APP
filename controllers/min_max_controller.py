from flask import Blueprint, redirect, render_template, request, jsonify, send_file, flash, session, url_for
from werkzeug.utils import secure_filename
import pandas as pd
import os
from io import BytesIO
from database import db
from models import ItemMaster
import logging

min_max_bp = Blueprint('min_max', __name__, template_folder='templates')

# Ensure upload folder exists
UPLOAD_FOLDER = 'Uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

# Logging setup
logging.basicConfig(level=logging.DEBUG)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@min_max_bp.route('/min_max_calculator', methods=['GET', 'POST']) 
def min_max_calculator():
    if request.method == 'GET':
        return render_template('min_max/list.html', current_page="min_max_calculator")
    
    try:
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        if not allowed_file(file.filename):
            flash('Invalid file type. Only .xlsx or .xls allowed', 'error')
            return redirect(request.url)

        # Save file temporarily
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # Read Excel file
        df = pd.read_excel(file_path)
        logging.debug(f"Excel file columns: {list(df.columns)}")
        logging.debug(f"Excel file shape: {df.shape}")
        
        required_columns = ['product_code', 'product_description', 'quantity_sold']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            flash(f'Excel file must contain the following columns: {", ".join(required_columns)}. Missing: {missing_columns}', 'error')
            os.remove(file_path)
            return redirect(request.url)

        # Aggregate duplicates by product_code and product_description, summing quantity_sold
        df = df.groupby(['product_code', 'product_description'], as_index=False)['quantity_sold'].sum()
        logging.debug(f"Aggregated data shape: {df.shape}")
        logging.debug(f"Aggregated data: {df.to_dict(orient='records')}")

        # Get parameters from form
        lead_time = float(request.form.get('lead_time', 5))
        safety_stock_days = float(request.form.get('safety_stock_days', 2))
        buffer_days = float(request.form.get('buffer_days', 10))

        # Query ItemMaster for units_per_bag and update min_level, max_level
        results = []
        logging.debug(f"Processing {len(df)} unique products...")
        
        for _, row in df.iterrows():
            product_code = row['product_code']
            product_description = row['product_description']
            quantity_sold_boxes = row['quantity_sold']
            
            logging.debug(f"Processing product: {product_code} - {product_description} - Qty: {quantity_sold_boxes}")
            
            # Query ItemMaster
            item = ItemMaster.query.filter_by(item_code=str(product_code)).first()
            if not item or not item.units_per_bag:
                logging.debug(f"Item not found or units_per_bag missing for {product_code}")
                results.append({
                    'product_code': product_code,
                    'product_description': product_description,
                    'quantity_sold_boxes': quantity_sold_boxes,
                    'error': 'Item not found or units_per_bag missing'
                })
                continue

            # Convert boxes to units
            units_sold = quantity_sold_boxes * item.units_per_bag
            
            # Calculate min/max (assuming quantity_sold is daily demand)
            min_stock = (units_sold * lead_time) + (units_sold * safety_stock_days)
            max_stock = min_stock + (units_sold * buffer_days)

            # Update ItemMaster with calculated min_level and max_level
            item.min_level = round(min_stock, 2)
            item.max_level = round(max_stock, 2)
            db.session.commit()
            logging.debug(f"Updated ItemMaster for {product_code}: min_level={item.min_level}, max_level={item.max_level}")

            logging.debug(f"Calculated for {product_code}: Units Sold={units_sold}, Min={min_stock}, Max={max_stock}")

            results.append({
                'product_code': product_code,
                'product_description': product_description,
                'quantity_sold_boxes': quantity_sold_boxes,
                'units_per_bag': item.units_per_bag,
                'units_sold': units_sold,
                'min_stock': round(min_stock, 2),
                'max_stock': round(max_stock, 2)
            })

        # Clean up uploaded file
        os.remove(file_path)

        # Save results to session for download
        session['min_max_results'] = results
        logging.debug(f"Generated {len(results)} results")
        logging.debug(f"Results: {results}")
        
        # Add flash message to show results count
        flash(f'Successfully processed and updated {len(results)} items', 'success')
        
        return render_template('min_max/list.html', 
                             results=results, 
                             current_page="min_max_calculator")

    except Exception as e:
        logging.error(f"Error processing file: {str(e)}")
        db.session.rollback()  # Rollback on error to prevent partial updates
        flash(f'Error: {str(e)}', 'error')
        return redirect(request.url)

@min_max_bp.route('/download_min_max')
def download_min_max():
    try:
        results = session.get('min_max_results', [])
        if not results:
            flash('No results available to download', 'error')
            return redirect(url_for('min_max.min_max_calculator'))

        # Convert results to CSV
        output = BytesIO()
        df = pd.DataFrame(results)
        df.to_csv(output, index=False)
        output.seek(0)

        return send_file(output, mimetype='text/csv', 
                        download_name='min_max_results.csv', 
                        as_attachment=True)
    except Exception as e:
        logging.error(f"Error generating download: {str(e)}")
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('min_max.min_max_calculator'))