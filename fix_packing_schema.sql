-- Fix Packing Table Schema
-- This script updates the packing table to use the new composite primary key

-- Step 1: Drop the old unique constraint if it exists
ALTER TABLE packing DROP INDEX uq_packing_week_product;

-- Step 2: Drop the old primary key
ALTER TABLE packing DROP PRIMARY KEY;

-- Step 3: Add the new composite primary key
ALTER TABLE packing ADD PRIMARY KEY (week_commencing, packing_date, product_code, machinery);

-- Step 4: Verify the changes
SHOW CREATE TABLE packing; 