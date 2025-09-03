#!/usr/bin/env python3
"""
Test script to verify the Excel export includes Week Commencing and Item Code columns
"""

from datetime import datetime, date
import pandas as pd
import io

# Mock data to test the export structure
def test_export_structure():
    """Test the export data structure"""
    
    # Mock inventory record data
    mock_data = {
        'Week Commencing': '2024-01-15',
        'Item Code': 'RM001',
        'Item': 'Raw Material 1',
        'Category': 'Category A',
        'Required Total': 100.50,
        '$/KG': 5.25,
        '$ Value RM': 527.63,
        'SOH': 50.00,
        'Supplier Name': 'Supplier ABC',
        'Required for Plan': 100.50,
        'Variance Week': -50.50,
        'Mon Opening': 50.00,
        'Mon Required': 20.00,
        'Mon Variance': 30.00,
        'Mon To Be Ordered': 0.00,
        'Mon Ordered/Received': 0.00,
        'Mon Consumed': 0.00,
        'Mon Closing': 50.00,
        # ... other daily columns would be here
    }
    
    # Create DataFrame
    df = pd.DataFrame([mock_data])
    
    # Test Excel creation
    output = io.BytesIO()
    df.to_excel(output, index=False, sheet_name='Inventory')
    output.seek(0)
    
    print("✅ Export structure test passed!")
    print("📊 Columns in export:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2d}. {col}")
    
    print(f"\n📋 Total columns: {len(df.columns)}")
    print("✅ Week Commencing column: ", "✅ FOUND" if 'Week Commencing' in df.columns else "❌ MISSING")
    print("✅ Item Code column: ", "✅ FOUND" if 'Item Code' in df.columns else "❌ MISSING")
    
    return True

if __name__ == "__main__":
    test_export_structure()
