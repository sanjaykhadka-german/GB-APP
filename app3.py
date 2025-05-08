import pandas as pd
from sqlalchemy import create_engine
import os
import datetime

# --- CONFIGURATION ---
excel_file_path = "Production_Plan_1.0.xlsm"  # Path to your Excel file
sheet_name = "pack"                           # Name of the sheet to read

# MySQL connection details
db_user = "root"
db_pass = "german"
db_host = "localhost"
db_name = "gbdb"
table_name = "packing"                        # Name of your MySQL table

# --- READ EXCEL ---
if not os.path.exists(excel_file_path):
    print(f"Error: File '{excel_file_path}' not found")
    exit(1)

try:
    df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
except Exception as e:
    print(f"Error reading Excel file: {e}")
    exit(1)

# --- PREPARE DATAFRAME ---

# Rename columns if needed (adjust as per your Excel headers)
df = df.rename(columns={
    'product_code': 'product_code',
    'product_description': 'product_description',
    'avg_weight_per_unit': 'avg_weight_per_unit',
    'weekly_average': 'weekly_average'
})

# Add packing_date column with today's date
df['packing_date'] = datetime.date.today()

# Keep only the columns that match your MySQL table
df = df[['product_code', 'product_description', 'weekly_average', 'packing_date']]

# --- CONNECT TO MYSQL ---
engine = create_engine(f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}")

# --- INSERT DATA ---
try:
    df.to_sql(table_name, con=engine, if_exists='append', index=False)
    print("Data inserted successfully!")
except Exception as e:
    print(f"Error inserting data: {e}")
