import pandas as pd
from sqlalchemy import create_engine

# Replace these with your actual database credentials
DB_USER = "root"
DB_PASSWORD = "german"
DB_HOST = "localhost"
DB_NAME = "gbdb"

# Create the connection string for MySQL (adjust for other databases as needed)
conn_str = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# Create SQLAlchemy engine
engine = create_engine(conn_str)

# Read the 'joining' table into a pandas DataFrame
df = pd.read_sql_table('joining', engine)

# Save the DataFrame to an Excel file
df.to_excel('joining_export.xlsx', index=False, engine='openpyxl')

print("Successfully exported 'joining' table to joining_export.xlsx")
