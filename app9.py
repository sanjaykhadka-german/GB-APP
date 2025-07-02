# prompt: read the sheet name join in this excel and give a python script to insert this database 
# id, fg_code, fg_description, filling_code, filling_code_description, production_code, production_description, is_active, created_at, updated_at, fg_item_id, filling_item_id, production_item_id
# into this table

from sqlalchemy import create_engine, text
import pandas as pd

# Replace with your actual database connection details
# Example for SQLite:
# engine = create_engine('sqlite:///mydatabase.db')

# Example for PostgreSQL:
# engine = create_engine('postgresql://user:password@host:port/database')

# Example for MySQL:
# engine = create_engine('mysql+mysqlconnector://user:password@host:port/database')

# Read the specific sheet 'join' from the Excel file
try:
    df_join = pd.read_excel('/content/Production_Plan_1.0.xlsx', sheet_name='join')
except Exception as e:
    print(f"Error reading Excel file or sheet: {e}")
    # Exit or handle the error appropriately
    exit()


# --- Database Insertion ---

# Ensure you have defined your database connection 'engine' here
# For demonstration, let's assume you have a valid 'engine' object

# Optional: Rename columns in the DataFrame to match database table columns
# This is a good practice to avoid issues if Excel column names don't exactly match
df_join = df_join.rename(columns={
    'id': 'id',
    'fg_code': 'fg_code',
    'fg_description': 'fg_description',
    'filling_code': 'filling_code',
    'filling_code_description': 'filling_code_description',
    'production_code': 'production_code',
    'production_description': 'production_description',
    'is_active': 'is_active',
    'created_at': 'created_at',
    'updated_at': 'updated_at',
    'fg_item_id': 'fg_item_id',
    'filling_item_id': 'filling_item_id',
    'production_item_id': 'production_item_id'
})

# Insert data into the database table named 'your_table_name'
# Replace 'your_table_name' with the actual name of your database table
try:
    with engine.connect() as connection:
        # Define the INSERT statement. Adjust column names if they are different in your table.
        insert_sql = text("""
        INSERT INTO your_table_name (
            id, fg_code, fg_description, filling_code, filling_code_description,
            production_code, production_description, is_active, created_at,
            updated_at, fg_item_id, filling_item_id, production_item_id
        ) VALUES (
            :id, :fg_code, :fg_description, :filling_code, :filling_code_description,
            :production_code, :production_description, :is_active, :created_at,
            :updated_at, :fg_item_id, :filling_item_id, :production_item_id
        )
        """)

        # Iterate over DataFrame rows and execute INSERT statements
        for index, row in df_join.iterrows():
            try:
                connection.execute(insert_sql, **row.to_dict())
            except Exception as e:
                print(f"Error inserting row {index}: {e}")
                # You might want to log the row data and continue or break
                # print(row.to_dict())

        # Commit the transaction
        connection.commit()
        print("Data inserted successfully!")

except NameError:
    print("Error: Database engine 'engine' is not defined. Please configure your database connection.")
except Exception as e:
    print(f"An error occurred during database insertion: {e}")

