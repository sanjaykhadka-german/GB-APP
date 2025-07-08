-- Disable foreign key checks
SET FOREIGN_KEY_CHECKS = 0;

-- Truncate tables in correct order (child tables first)
TRUNCATE TABLE raw_material_report_table;
TRUNCATE TABLE usage_report_table;
TRUNCATE TABLE production;
TRUNCATE TABLE filling;
TRUNCATE TABLE packing;
TRUNCATE TABLE soh;
TRUNCATE TABLE raw_material_stocktake;

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- Verify tables are empty
SELECT 'raw_material_report_table' as table_name, COUNT(*) as count FROM raw_material_report_table
UNION ALL
SELECT 'usage_report_table', COUNT(*) FROM usage_report_table
UNION ALL
SELECT 'production', COUNT(*) FROM production
UNION ALL
SELECT 'filling', COUNT(*) FROM filling
UNION ALL
SELECT 'packing', COUNT(*) FROM packing
UNION ALL
SELECT 'soh', COUNT(*) FROM soh
UNION ALL
SELECT 'raw_material_stocktake', COUNT(*) FROM raw_material_stocktake; 