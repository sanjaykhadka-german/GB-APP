-- First backup the data to raw_material_report
INSERT INTO raw_material_report (
    production_date,
    week_commencing,
    raw_material,
    raw_material_id,
    meat_required,
    created_at
)
SELECT DISTINCT
    rm.week_commencing as production_date,
    rm.week_commencing,
    raw.raw_material,
    raw.id as raw_material_id,
    rm.kg_per_batch * rm.percentage / 100 as meat_required,
    NOW() as created_at
FROM recipe_master rm
JOIN raw_materials raw ON rm.raw_material_id = raw.id
WHERE rm.week_commencing IS NOT NULL
AND NOT EXISTS (
    SELECT 1 
    FROM raw_material_report rr 
    WHERE rr.week_commencing = rm.week_commencing
    AND rr.raw_material_id = raw.id
);

-- Now drop the week_commencing column
ALTER TABLE recipe_master DROP COLUMN week_commencing; 