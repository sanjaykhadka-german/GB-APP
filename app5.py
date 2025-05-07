import pandas as pd
from sqlalchemy import create_engine
import os

# --- CONFIGURATION ---
excel_file_path = "Production_Plan_1.0.xlsm"
sheet_name = "soh_table"

# MySQL connection
db_user = "root"
db_pass = "german"
db_host = "localhost"
db_name = "gbdb"
table_name = "soh"

# --- READ EXCEL ---
if not os.path.exists(excel_file_path):
    print(f"Error: File '{excel_file_path}' not found")
    exit(1)

df = pd.read_excel(excel_file_path, sheet_name=sheet_name)

# Print columns to debug
print("Excel columns:", df.columns)

# Rename columns to match DB
df = df.rename(columns={
    'FG Code': 'fg_code',         # Excel column name : DB column name
    'Description': 'description'
})

# Add missing columns with default values
for col in ['id','soh_dispatch_boxes', 'soh_dispatch_units', 'soh_packing_boxes', 'soh_packing_units', 'soh_total_boxes', 'soh_total_units']:
    if col not in df.columns:
        df[col] = 0.0  # Set default to 0.0 for float columns

# Reorder columns, EXCLUDING 'id' since it's auto-incremented by the database
df = df[['id','fg_code', 'description', 'soh_dispatch_boxes', 'soh_dispatch_units', 'soh_packing_boxes', 'soh_packing_units', 'soh_total_boxes', 'soh_total_units']]

# --- CONNECT TO MYSQL ---
engine = create_engine(f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}")

# --- INSERT DATA ---
try:
    df.to_sql(table_name, con=engine, if_exists='append', index=False)
    print("Data inserted successfully!")
except Exception as e:
    print(f"Error inserting data: {e}")