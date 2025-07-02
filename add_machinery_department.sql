-- Add machinery_id and department_id to SOH
ALTER TABLE soh 
ADD COLUMN machinery_id INT NULL,
ADD COLUMN department_id INT NULL,
ADD CONSTRAINT fk_soh_machinery FOREIGN KEY (machinery_id) REFERENCES machinery(machineID) ON DELETE SET NULL,
ADD CONSTRAINT fk_soh_department FOREIGN KEY (department_id) REFERENCES department(department_id) ON DELETE SET NULL;

-- Add machinery_id and department_id to Filling
ALTER TABLE filling 
ADD COLUMN machinery_id INT NULL,
ADD COLUMN department_id INT NULL,
ADD CONSTRAINT fk_filling_machinery FOREIGN KEY (machinery_id) REFERENCES machinery(machineID) ON DELETE SET NULL,
ADD CONSTRAINT fk_filling_department FOREIGN KEY (department_id) REFERENCES department(department_id) ON DELETE SET NULL;

-- Update Packing table (already has machinery column)
ALTER TABLE packing 
ADD COLUMN department_id INT NULL,
ALGORITHM=INPLACE;

ALTER TABLE packing
CHANGE COLUMN machinery machinery_id INT NULL,
ALGORITHM=INPLACE;

ALTER TABLE packing
ADD CONSTRAINT fk_packing_machinery FOREIGN KEY (machinery_id) REFERENCES machinery(machineID) ON DELETE SET NULL,
ADD CONSTRAINT fk_packing_department FOREIGN KEY (department_id) REFERENCES department(department_id) ON DELETE SET NULL;

-- Add machinery_id and department_id to Production
ALTER TABLE production 
ADD COLUMN machinery_id INT NULL,
ADD COLUMN department_id INT NULL,
ADD CONSTRAINT fk_production_machinery FOREIGN KEY (machinery_id) REFERENCES machinery(machineID) ON DELETE SET NULL,
ADD CONSTRAINT fk_production_department FOREIGN KEY (department_id) REFERENCES department(department_id) ON DELETE SET NULL; 