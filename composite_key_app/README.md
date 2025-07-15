# Composite Key Item Master System

A modern Flask-based manufacturing item management system that implements composite key constraints to support product variants with the same item code but different descriptions.

## Problem Solved

This system addresses the challenge of managing items where the same item code needs to have different variants:

- **1007 - HF Pulled pork - WIP**
- **1007 - GB Pulled Pork - WIP**

Traditional systems with unique constraints on `item_code` alone cannot handle this scenario. Our solution uses a composite unique constraint on `(item_code, description)`.

## Features

### 🔑 Composite Key Implementation
- Unique constraint on `(item_code, description)` instead of `item_code` alone
- Allows multiple variants of the same item code
- Prevents exact duplicates while supporting valid variants
- Maintains data integrity

### 📊 Comprehensive Item Management
- Full CRUD operations for items
- Support for all item types: RM, WIP, WIPF, FG, PKG
- Advanced search functionality
- Pagination and filtering
- Self-referencing relationships for FG composition

### 🧪 Recipe Management
- Bill of Materials (BOM) management
- Component-to-recipe relationships
- Automatic percentage calculations
- Bulk recipe creation
- Component usage tracking

### 🎨 Modern Web Interface
- Bootstrap 5 responsive design
- Interactive dashboards
- Real-time statistics
- Educational modals explaining composite key concepts
- User-friendly forms and tables

## Database Schema

### ItemMaster Table
```sql
CREATE TABLE item_master (
    id INT PRIMARY KEY AUTO_INCREMENT,
    item_code VARCHAR(50) NOT NULL,
    description VARCHAR(255) NOT NULL,
    item_type_id INT NOT NULL,
    -- ... other fields ...
    UNIQUE KEY uq_item_code_description (item_code, description),
    INDEX idx_item_code (item_code)
);
```

### Key Relationships
- **Self-referencing**: FG → WIP → WIPF relationships
- **Recipe Components**: WIP items linked to their RM/WIP components
- **Lookup Tables**: ItemType, Category, Department, UOM

## Installation & Setup

### Prerequisites
- Python 3.8+
- MySQL 5.7+ or MariaDB 10.3+
- pip (Python package installer)

### 1. Clone and Setup Virtual Environment
```bash
git clone <repository-url>
cd composite_key_app
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Database Configuration
Create a `.env` file in the project root:
```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=mysql://username:password@localhost/composite_key_db
FLASK_ENV=development
FLASK_DEBUG=1
```

### 4. Create Database
```sql
CREATE DATABASE composite_key_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. Initialize Database
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 6. Seed Initial Data (Optional)
```bash
python seed_data.py
```

### 7. Run the Application
```bash
python app.py
```

Visit `http://localhost:5000` to access the application.

## API Endpoints

### Items API
- `GET /api/items/` - List all items with pagination and search
- `POST /api/items/` - Create new item
- `GET /api/items/<id>` - Get specific item
- `PUT /api/items/<id>` - Update item
- `DELETE /api/items/<id>` - Delete item
- `GET /api/items/by-code/<code>` - Get all variants of an item code
- `GET /api/items/by-code-description` - Get item by code and description
- `GET /api/items/search` - Search items

### Recipes API
- `GET /api/recipes/` - List all recipes
- `POST /api/recipes/` - Create recipe component
- `GET /api/recipes/<id>` - Get recipe component
- `PUT /api/recipes/<id>` - Update recipe component
- `DELETE /api/recipes/<id>` - Delete recipe component
- `GET /api/recipes/wip/<id>` - Get complete recipe for WIP item

### Lookup APIs
- `GET /api/items/types` - Get all item types
- `GET /api/items/categories` - Get all categories
- `GET /api/items/departments` - Get all departments
- `GET /api/items/uoms` - Get all units of measure

## Usage Examples

### Creating Items with Same Code, Different Descriptions

```python
# This will work - different descriptions
item1 = ItemMaster(
    item_code="1007",
    description="HF Pulled pork - WIP",
    item_type_id=2  # WIP
)

item2 = ItemMaster(
    item_code="1007", 
    description="GB Pulled Pork - WIP",
    item_type_id=2  # WIP
)

# This will fail - exact duplicate
item3 = ItemMaster(
    item_code="1007",
    description="HF Pulled pork - WIP",  # Same as item1
    item_type_id=2
)
```

### Querying Items

```python
# Find specific item by code and description
item = ItemMaster.find_by_code_and_description("1007", "HF Pulled pork - WIP")

# Find all variants of an item code
variants = ItemMaster.find_variants_by_code("1007")

# Search by code or description
results = ItemMaster.search_items("pulled pork")
```

### Creating Recipes

```python
# Create recipe components for a WIP item
wip_item = ItemMaster.find_by_code_and_description("1007", "HF Pulled pork - WIP")

# Add components
component1 = RecipeMaster(
    recipe_wip_id=wip_item.id,
    component_item_id=pork_shoulder.id,
    quantity_kg=100.0,
    sequence_number=1
)

component2 = RecipeMaster(
    recipe_wip_id=wip_item.id,
    component_item_id=seasoning.id,
    quantity_kg=5.0,
    sequence_number=2
)
```

## Project Structure

```
composite_key_app/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .env.example          # Environment variables template
├── models/               # Database models
│   ├── __init__.py
│   ├── item_master.py    # ItemMaster and lookup models
│   └── recipe_master.py  # RecipeMaster model
├── controllers/          # API controllers/blueprints
│   ├── __init__.py
│   ├── item_controller.py
│   └── recipe_controller.py
├── templates/            # HTML templates
│   ├── base.html        # Base template
│   ├── index.html       # Dashboard
│   ├── items/
│   │   └── index.html   # Items management page
│   └── recipes/
│       └── index.html   # Recipes management page
├── static/              # CSS, JS, images
├── migrations/          # Database migrations
├── tests/               # Unit tests
└── scripts/             # Utility scripts
```

## Key Design Decisions

### 1. Composite Key Strategy
- **Decision**: Use `UniqueConstraint('item_code', 'description')` 
- **Benefit**: Supports product variants while maintaining data integrity
- **Trade-off**: Requires updating queries that previously relied on unique item_code

### 2. Self-Referencing Relationships
- **Decision**: Use foreign keys within ItemMaster for FG composition
- **Benefit**: Flexible hierarchy support (FG → WIP → WIPF)
- **Implementation**: Careful handling of circular references

### 3. Separate Recipe Table
- **Decision**: Dedicated RecipeMaster table for BOM
- **Benefit**: Clean separation of concerns, flexible recipe structures
- **Features**: Automatic percentage calculations, sequence ordering

## Testing

### Run Unit Tests
```bash
python -m pytest tests/
```

### Run Integration Tests
```bash
python -m pytest tests/integration/
```

### Test Coverage
```bash
python -m pytest --cov=. tests/
```

## Migration from Existing Systems

### From Single Unique Key System
1. **Backup existing data**
2. **Identify potential conflicts** (same code, different descriptions)
3. **Run migration script**:
   ```bash
   python migrate_to_composite_key.py
   ```
4. **Update application queries**
5. **Test thoroughly**

### Migration Script Example
```python
def migrate_to_composite_key():
    # Remove existing unique constraint
    db.session.execute(text("ALTER TABLE item_master DROP INDEX item_code"))
    
    # Add composite constraint
    db.session.execute(text("""
        ALTER TABLE item_master 
        ADD CONSTRAINT uq_item_code_description 
        UNIQUE (item_code, description)
    """))
    
    # Recreate index for performance
    db.session.execute(text("CREATE INDEX idx_item_code ON item_master (item_code)"))
    
    db.session.commit()
```

## Performance Considerations

### Indexing Strategy
- **Primary Index**: `(item_code, description)` for unique constraint
- **Secondary Index**: `item_code` for variant lookups
- **Foreign Key Indexes**: Automatic indexes on all FK relationships

### Query Optimization
- Use specific queries when possible: `find_by_code_and_description()`
- Implement pagination for large datasets
- Consider caching for lookup tables

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Ensure all tests pass: `python -m pytest`
5. Commit your changes: `git commit -am 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For questions, issues, or feature requests:

1. **Documentation**: Check this README and code comments
2. **Issues**: Create a GitHub issue with detailed description
3. **Discussions**: Use GitHub Discussions for questions and ideas

## Roadmap

### Phase 1 (Current)
- ✅ Composite key implementation
- ✅ Basic CRUD operations
- ✅ Web interface
- ✅ Recipe management

### Phase 2 (Planned)
- [ ] Advanced reporting
- [ ] Data import/export
- [ ] User authentication
- [ ] Audit logging

### Phase 3 (Future)
- [ ] REST API documentation (OpenAPI/Swagger)
- [ ] Mobile responsive improvements
- [ ] Real-time notifications
- [ ] Advanced search with filters