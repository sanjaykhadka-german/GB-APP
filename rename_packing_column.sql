-- SQL script to rename weekly_average column to calculation_factor in packing table
-- Run this script on your MySQL database

-- Check current table structure
DESCRIBE packing;

-- Rename the column from weekly_average to calculation_factor
ALTER TABLE packing 
CHANGE COLUMN weekly_average calculation_factor FLOAT DEFAULT 0.0;

-- Verify the change
DESCRIBE packing;

-- Optional: Check if there are any existing records and their values
SELECT COUNT(*) as total_records FROM packing;
SELECT COUNT(*) as records_with_calculation_factor FROM packing WHERE calculation_factor IS NOT NULL;

COMMIT; 