ALTER TABLE production
ADD COLUMN total_planned FLOAT DEFAULT 0.0,
ADD COLUMN monday_planned FLOAT DEFAULT 0.0,
ADD COLUMN tuesday_planned FLOAT DEFAULT 0.0,
ADD COLUMN wednesday_planned FLOAT DEFAULT 0.0,
ADD COLUMN thursday_planned FLOAT DEFAULT 0.0,
ADD COLUMN friday_planned FLOAT DEFAULT 0.0,
ADD COLUMN saturday_planned FLOAT DEFAULT 0.0,
ADD COLUMN sunday_planned FLOAT DEFAULT 0.0; 