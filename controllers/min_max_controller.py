from flask import Blueprint, request, render_template, jsonify
import pandas as pd
import io
from datetime import datetime

min_max_bp = Blueprint('min_max', __name__, template_folder='templates')

@min_max_bp.route('/min_max/')
def min_max_calculator():
    """Render the Min/Max calculator upload page."""
    return render_template('min_max/list.html', current_page='min_max_calculator')

@min_max_bp.route('/min_max_calculator')
def min_max_calculator_alias():
    return render_template('min_max/list.html', current_page='min_max_calculator')

@min_max_bp.route('/min_max/calculate', methods=['POST'])
def calculate_min_max():
    """
    Handle the uploaded file and compute per-product weekly totals, then min/max across weeks.

    Supports either a precomputed ISO week column (e.g., ISOWEEKNUM) or a date column
    (e.g., OrderCheckoutDate) from which ISO week is derived.
    Returns: { success: true, results: { product -> { min, max } } }
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        try:
            # Read the Excel file
            df = pd.read_excel(io.BytesIO(file.read()), engine='openpyxl')
            df.columns = [str(col).strip() for col in df.columns]

            # Define acceptable column name variants (includes Excel-style columns)
            column_variants = {
                'product': [
                    'Product Code Description', 'Product Description', 'Product', 'Product Name', 'Item', 'Item Description'
                ],
                'weight': [
                    'TotalWeight', 'Total Weight', 'Total_Weight', 'Weight', 'Total Kg', 'Total KG', 'Kg', 'KG'
                ],
                'date': [
                    'OrderCheckoutDate', 'Order Checkout Date', 'Date', 'Transaction Date', 'Created Date', 'Order Date', 'Delivery Date'
                ],
                'week': [
                    'ISOWEEKNUM', 'ISO Week', 'ISO Week Number', 'ISOWeekNum', 'ISO WeekNum',
                    'Week', 'Week Number', 'Week No', 'Week_No'
                ]
            }

            def find_column_possibilities(possible_names):
                lowered = {c.lower().strip(): c for c in df.columns}
                for name in possible_names:
                    key = str(name).lower().strip()
                    if key in lowered:
                        return lowered[key]
                return None

            def fuzzy_find_product_column() -> str | None:
                candidates = [str(c) for c in df.columns]
                for c in candidates:
                    normalized = c.lower()
                    if ('product' in normalized or 'item' in normalized) and (
                        'description' in normalized or 'code' in normalized or 'name' in normalized
                    ):
                        return c
                for c in candidates:
                    if c.lower().strip() in {'product', 'item', 'description'}:
                        return c
                return None

            def fuzzy_find_weight_column() -> str | None:
                candidates = [str(c) for c in df.columns]
                for c in candidates:
                    normalized = c.lower().replace(' ', '')
                    if 'total' in normalized and ('weight' in normalized or 'kg' in normalized):
                        return c
                for c in candidates:
                    if c.lower().strip() in {'totalweight', 'weight', 'kg'}:
                        return c
                return None

            def fuzzy_find_date_column() -> str | None:
                candidates = [str(c) for c in df.columns]
                for c in candidates:
                    normalized = c.lower()
                    if 'date' in normalized:
                        return c
                return None

            def fuzzy_find_week_column() -> str | None:
                candidates = [str(c) for c in df.columns]
                for c in candidates:
                    normalized = c.lower().replace(' ', '')
                    if 'week' in normalized:
                        return c
                return None

            # Find required columns
            product_col = find_column_possibilities(column_variants['product']) or fuzzy_find_product_column()
            weight_col = find_column_possibilities(column_variants['weight']) or fuzzy_find_weight_column()
            date_col = find_column_possibilities(column_variants['date']) or fuzzy_find_date_column()
            week_col = find_column_possibilities(column_variants['week']) or fuzzy_find_week_column()

            if not product_col or not weight_col:
                return jsonify({
                    'error': 'Missing required columns. Expected product and weight columns.',
                    'details': {
                        'found_columns': list(map(str, df.columns)),
                        'expected_product_any_of': column_variants['product'],
                        'expected_weight_any_of': column_variants['weight']
                    }
                }), 400

            # Ensure weight column is numeric
            df[weight_col] = pd.to_numeric(df[weight_col], errors='coerce')
            df = df.dropna(subset=[product_col, weight_col])

            # Determine week source: prefer explicit week, else derive from date
            if not week_col and date_col:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                iso = df[date_col].dt.isocalendar()
                df['__week_key__'] = (
                    iso['year'].astype(int).astype(str) + '-W' + iso['week'].astype(int).astype(str).str.zfill(2)
                )
            elif week_col:
                # Use provided week column as string key to avoid numeric NaN issues
                df['__week_key__'] = df[week_col].astype(str).str.strip()
            else:
                return jsonify({
                    'error': 'Missing week/date information. Provide ISOWEEKNUM or a date column like OrderCheckoutDate.',
                    'details': {
                        'found_columns': list(map(str, df.columns)),
                        'expected_week_any_of': column_variants['week'],
                        'expected_date_any_of': column_variants['date']
                    }
                }), 400

            # Drop rows without computed week key
            df = df.dropna(subset=['__week_key__'])

            # Aggregate weekly sums per product
            weekly_sums = (
                df.groupby([product_col, '__week_key__'])[weight_col]
                .sum()
                .reset_index(name='weekly_total')
            )

            # Build a complete product x week matrix and fill missing with 0
            all_products = (
                df[product_col].dropna().astype(str).unique().tolist()
            )
            all_weeks = (
                df['__week_key__'].dropna().astype(str).unique().tolist()
            )

            pivot = weekly_sums.pivot_table(
                index=product_col,
                columns='__week_key__',
                values='weekly_total',
                aggfunc='sum'
            )
            # Ensure all products and weeks are present; fill missing with 0
            pivot = pivot.reindex(index=all_products, columns=all_weeks).fillna(0)

            # Compute min/max across weeks for each product, including zero-weeks
            min_series = pivot.min(axis=1)
            max_series = pivot.max(axis=1)

            results = {prod: {'min': float(min_series.loc[prod]), 'max': float(max_series.loc[prod])}
                       for prod in pivot.index}

            return jsonify({'success': True, 'results': results})

        except Exception as e:
            return jsonify({'error': str(e)}), 500