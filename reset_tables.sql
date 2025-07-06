USE gbdb;

-- First disable foreign key checks
SET FOREIGN_KEY_CHECKS = 0;

-- Truncate tables in correct order
TRUNCATE TABLE raw_material_report_table;
TRUNCATE TABLE usage_report_table;
TRUNCATE TABLE production;
TRUNCATE TABLE filling;
TRUNCATE TABLE packing;
TRUNCATE TABLE raw_material_stocktake;
TRUNCATE TABLE soh;

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- Reset auto-increment values
ALTER TABLE production AUTO_INCREMENT = 1;
ALTER TABLE filling AUTO_INCREMENT = 1;
ALTER TABLE packing AUTO_INCREMENT = 1;
ALTER TABLE raw_material_stocktake AUTO_INCREMENT = 1;
ALTER TABLE soh AUTO_INCREMENT = 1; 