-- Add price_per_uom column to item_master table
-- Run this SQL script in your MySQL database (gbdb)

USE gbdb;

ALTER TABLE item_master 
ADD COLUMN price_per_uom DECIMAL(10,2) DEFAULT NULL 
COMMENT 'Price per unit of measure';

-- Verify the column was added
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE() 
AND TABLE_NAME = 'item_master' 
AND COLUMN_NAME = 'price_per_uom'; 