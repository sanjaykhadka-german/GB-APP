USE gbdb;

DROP TABLE IF EXISTS inventory;

CREATE TABLE inventory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    week_commencing DATE NOT NULL,
    item_id INT NOT NULL,
    required_total FLOAT DEFAULT 0.0,
    price_per_kg FLOAT DEFAULT 0.0,
    value_required FLOAT DEFAULT 0.0,
    current_stock FLOAT DEFAULT 0.0,
    supplier_name VARCHAR(255),
    required_for_plan FLOAT DEFAULT 0.0,
    variance_for_week FLOAT DEFAULT 0.0,
    
    -- Monday columns
    monday_opening_stock FLOAT DEFAULT 0.0,
    monday_required_kg FLOAT DEFAULT 0.0,
    monday_variance FLOAT DEFAULT 0.0,
    monday_to_be_ordered FLOAT DEFAULT 0.0,
    monday_ordered_received FLOAT DEFAULT 0.0,
    monday_consumed_kg FLOAT DEFAULT 0.0,
    monday_closing_stock FLOAT DEFAULT 0.0,
    
    -- Tuesday columns
    tuesday_opening_stock FLOAT DEFAULT 0.0,
    tuesday_required_kg FLOAT DEFAULT 0.0,
    tuesday_variance FLOAT DEFAULT 0.0,
    tuesday_to_be_ordered FLOAT DEFAULT 0.0,
    tuesday_ordered_received FLOAT DEFAULT 0.0,
    tuesday_consumed_kg FLOAT DEFAULT 0.0,
    tuesday_closing_stock FLOAT DEFAULT 0.0,
    
    -- Wednesday columns
    wednesday_opening_stock FLOAT DEFAULT 0.0,
    wednesday_required_kg FLOAT DEFAULT 0.0,
    wednesday_variance FLOAT DEFAULT 0.0,
    wednesday_to_be_ordered FLOAT DEFAULT 0.0,
    wednesday_ordered_received FLOAT DEFAULT 0.0,
    wednesday_consumed_kg FLOAT DEFAULT 0.0,
    wednesday_closing_stock FLOAT DEFAULT 0.0,
    
    -- Thursday columns
    thursday_opening_stock FLOAT DEFAULT 0.0,
    thursday_required_kg FLOAT DEFAULT 0.0,
    thursday_variance FLOAT DEFAULT 0.0,
    thursday_to_be_ordered FLOAT DEFAULT 0.0,
    thursday_ordered_received FLOAT DEFAULT 0.0,
    thursday_consumed_kg FLOAT DEFAULT 0.0,
    thursday_closing_stock FLOAT DEFAULT 0.0,
    
    -- Friday columns
    friday_opening_stock FLOAT DEFAULT 0.0,
    friday_required_kg FLOAT DEFAULT 0.0,
    friday_variance FLOAT DEFAULT 0.0,
    friday_to_be_ordered FLOAT DEFAULT 0.0,
    friday_ordered_received FLOAT DEFAULT 0.0,
    friday_consumed_kg FLOAT DEFAULT 0.0,
    friday_closing_stock FLOAT DEFAULT 0.0,
    
    -- Saturday columns
    saturday_opening_stock FLOAT DEFAULT 0.0,
    saturday_required_kg FLOAT DEFAULT 0.0,
    saturday_variance FLOAT DEFAULT 0.0,
    saturday_to_be_ordered FLOAT DEFAULT 0.0,
    saturday_ordered_received FLOAT DEFAULT 0.0,
    saturday_consumed_kg FLOAT DEFAULT 0.0,
    saturday_closing_stock FLOAT DEFAULT 0.0,
    
    -- Sunday columns
    sunday_opening_stock FLOAT DEFAULT 0.0,
    sunday_required_kg FLOAT DEFAULT 0.0,
    sunday_variance FLOAT DEFAULT 0.0,
    sunday_to_be_ordered FLOAT DEFAULT 0.0,
    sunday_ordered_received FLOAT DEFAULT 0.0,
    sunday_consumed_kg FLOAT DEFAULT 0.0,
    sunday_closing_stock FLOAT DEFAULT 0.0,
    
    FOREIGN KEY (item_id) REFERENCES item_master(id)
); 