import pandas as pd
from sqlalchemy import create_engine
import os

# --- CONFIGURATION ---
excel_file_path = "Production_Plan_1.0.xlsm"  # Change to your file
sheet_name = "pack"  # Change if your sheet has a different name

# MySQL connection (update with your details)
db_user = "root"
db_pass = "german"
db_host = "localhost"
db_name = "gbdb"
table_name = "packing"  # Change to your actual table name

# --- READ EXCEL ---
if not os.path.exists(excel_file_path):
    print(f"Error: File '{excel_file_path}' not found")
    exit(1)

df = pd.read_excel(excel_file_path, sheet_name=sheet_name)

# Make sure columns match your DB field names exactly
df = df.rename(columns={
    'product_code': 'product_code',
    'product_description': 'product_description',
    'weekly_average': 'weekly_average'
})

# Keep only the needed columns
df = df[['product_code', 'product_description', 'weekly_average']]

# --- CONNECT TO MYSQL ---
engine = create_engine(f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}")

# --- INSERT DATA ---
try:
    # Use if_exists='append' to add data without deleting existing rows
    df.to_sql(table_name, con=engine, if_exists='append', index=False)
    print("Data inserted successfully!")
except Exception as e:
    print(f"Error inserting data: {e}")
