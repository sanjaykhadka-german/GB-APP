USE gbdb;

DROP TABLE IF EXISTS inventory;

CREATE TABLE inventory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    week_commencing DATE NOT NULL,
    item_id INT NOT NULL,
    required_total FLOAT,
    category VARCHAR(100),
    price_per_kg FLOAT,
    value_required FLOAT,
    current_stock FLOAT,
    supplier_name VARCHAR(255),
    monday FLOAT DEFAULT 0,
    tuesday FLOAT DEFAULT 0,
    wednesday FLOAT DEFAULT 0,
    thursday FLOAT DEFAULT 0,
    friday FLOAT DEFAULT 0,
    saturday FLOAT DEFAULT 0,
    sunday FLOAT DEFAULT 0,
    required_for_plan FLOAT,
    variance_for_week FLOAT,
    variance FLOAT,
    to_be_ordered FLOAT,
    closing_stock FLOAT,
    FOREIGN KEY (item_id) REFERENCES item_master(id)
); 