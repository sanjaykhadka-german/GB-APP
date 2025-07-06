-- Disable foreign key checks
SET FOREIGN_KEY_CHECKS = 0;

-- Truncate all tables
TRUNCATE TABLE gbdb.soh;
SELECT COUNT(*) FROM gbdb.soh;

TRUNCATE TABLE gbdb.raw_material_stocktake;
SELECT COUNT(*) FROM gbdb.raw_material_stocktake;

TRUNCATE TABLE gbdb.packing;
SELECT COUNT(*) FROM gbdb.packing;

TRUNCATE TABLE gbdb.filling;
SELECT COUNT(*) FROM gbdb.filling;

TRUNCATE TABLE gbdb.production;
SELECT COUNT(*) FROM gbdb.production;

TRUNCATE TABLE gbdb.usage_report_table;
SELECT COUNT(*) FROM gbdb.usage_report_table;

TRUNCATE TABLE gbdb.raw_material_report_table;
SELECT COUNT(*) FROM gbdb.raw_material_report_table;

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- Verify all tables are empty
SELECT 'SOH' as table_name, COUNT(*) as count FROM gbdb.soh
UNION ALL
SELECT 'Raw Material Stocktake', COUNT(*) FROM gbdb.raw_material_stocktake
UNION ALL
SELECT 'Packing', COUNT(*) FROM gbdb.packing
UNION ALL
SELECT 'Filling', COUNT(*) FROM gbdb.filling
UNION ALL
SELECT 'Production', COUNT(*) FROM gbdb.production
UNION ALL
SELECT 'Usage Report', COUNT(*) FROM gbdb.usage_report_table
UNION ALL
SELECT 'Raw Material Report', COUNT(*) FROM gbdb.raw_material_report_table; 