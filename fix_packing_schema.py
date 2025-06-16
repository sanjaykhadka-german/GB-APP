#!/usr/bin/env python3
import mysql.connector
from mysql.connector import Error

def fix_packing_schema():
    try:
        # Connect to MySQL database
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='password',
            database='gb_app'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Check current table structure
            print("Checking current table structure...")
            cursor.execute("SHOW CREATE TABLE packing")
            table_info = cursor.fetchone()
            print("Current table structure:")
            print(table_info[1])
            
            # Drop the old unique constraint if it exists
            print("\nDropping old unique constraint...")
            try:
                cursor.execute("ALTER TABLE packing DROP INDEX uq_packing_week_product")
                print("Dropped uq_packing_week_product constraint")
            except Error as e:
                print(f"Could not drop uq_packing_week_product: {e}")
            
            # Drop the old primary key
            print("\nDropping old primary key...")
            try:
                cursor.execute("ALTER TABLE packing DROP PRIMARY KEY")
                print("Dropped old primary key")
            except Error as e:
                print(f"Could not drop primary key: {e}")
            
            # Add the new composite primary key
            print("\nAdding new composite primary key...")
            cursor.execute("""
                ALTER TABLE packing 
                ADD PRIMARY KEY (week_commencing, packing_date, product_code, machinery)
            """)
            print("Added new composite primary key")
            
            # Commit the changes
            connection.commit()
            print("\nSchema update completed successfully!")
            
            # Show the new table structure
            print("\nNew table structure:")
            cursor.execute("SHOW CREATE TABLE packing")
            new_table_info = cursor.fetchone()
            print(new_table_info[1])
            
    except Error as e:
        print(f"Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("\nDatabase connection closed.")

if __name__ == "__main__":
    fix_packing_schema() 