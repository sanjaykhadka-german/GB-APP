#!/usr/bin/env python3
"""
Script to rename weekly_average column to calculation_factor in packing table
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_database_connection():
    """Get database connection using environment variables"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'your_database_name'),
            user=os.getenv('DB_USER', 'your_username'),
            password=os.getenv('DB_PASSWORD', 'your_password'),
            port=os.getenv('DB_PORT', 3306)
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    try:
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = '{table_name}' 
            AND COLUMN_NAME = '{column_name}'
        """)
        return cursor.fetchone()[0] > 0
    except Error as e:
        print(f"Error checking column existence: {e}")
        return False

def rename_column():
    """Rename weekly_average to calculation_factor in packing table"""
    connection = get_database_connection()
    
    if not connection:
        print("Failed to connect to database")
        return False
    
    try:
        cursor = connection.cursor()
        
        # Check current table structure
        print("Checking current packing table structure...")
        cursor.execute("DESCRIBE packing")
        columns = cursor.fetchall()
        print("Current columns:")
        for col in columns:
            print(f"  - {col[0]} ({col[1]})")
        
        # Check if weekly_average column exists
        if column_exists(cursor, 'packing', 'weekly_average'):
            print("\nFound 'weekly_average' column. Renaming to 'calculation_factor'...")
            
            # Rename the column
            rename_sql = """
                ALTER TABLE packing 
                CHANGE COLUMN weekly_average calculation_factor FLOAT DEFAULT 0.0
            """
            cursor.execute(rename_sql)
            connection.commit()
            print("✅ Successfully renamed 'weekly_average' to 'calculation_factor'")
            
        elif column_exists(cursor, 'packing', 'calculation_factor'):
            print("Column 'calculation_factor' already exists. No action needed.")
            
        else:
            print("Neither 'weekly_average' nor 'calculation_factor' column found.")
            print("This might indicate a different table structure.")
        
        # Show updated table structure
        print("\nUpdated packing table structure:")
        cursor.execute("DESCRIBE packing")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[0]} ({col[1]})")
            
        return True
        
    except Error as e:
        print(f"Error during column rename: {e}")
        if connection.is_connected():
            connection.rollback()
        return False
        
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("\nDatabase connection closed.")

def main():
    """Main function"""
    print("=== Packing Table Column Rename Script ===")
    print("This script will rename 'weekly_average' to 'calculation_factor' in the packing table.")
    
    # Ask for confirmation
    response = input("\nDo you want to proceed? (y/N): ").strip().lower()
    if response != 'y':
        print("Operation cancelled.")
        return
    
    print("\nStarting column rename operation...")
    success = rename_column()
    
    if success:
        print("\n✅ Operation completed successfully!")
        print("Remember to update your application code to use 'calculation_factor' instead of 'weekly_average'")
    else:
        print("\n❌ Operation failed. Please check the error messages above.")

if __name__ == "__main__":
    main() 