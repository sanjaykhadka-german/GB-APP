#!/usr/bin/env python3
"""
Seed script to populate the database with initial data including lookup tables
and example items demonstrating the composite key functionality.
"""

from app import app, db
from models.item_master import ItemMaster, ItemType, Category, Department, UOM
from models.recipe_master import RecipeMaster

def seed_lookup_tables():
    """Populate lookup tables with initial data"""
    print("Seeding lookup tables...")
    
    # Item Types
    item_types = [
        {'type_name': 'RM', 'description': 'Raw Material'},
        {'type_name': 'WIP', 'description': 'Work in Progress'},
        {'type_name': 'WIPF', 'description': 'Work in Progress Finished'},
        {'type_name': 'FG', 'description': 'Finished Goods'},
        {'type_name': 'PKG', 'description': 'Packaging Material'}
    ]
    
    for type_data in item_types:
        existing = ItemType.query.filter_by(type_name=type_data['type_name']).first()
        if not existing:
            item_type = ItemType(**type_data)
            db.session.add(item_type)
    
    # Categories
    categories = [
        {'name': 'Meat Products', 'description': 'All meat-based products'},
        {'name': 'Seasonings', 'description': 'Spices and seasonings'},
        {'name': 'Additives', 'description': 'Food additives and preservatives'},
        {'name': 'Packaging', 'description': 'Packaging materials'}
    ]
    
    for cat_data in categories:
        existing = Category.query.filter_by(name=cat_data['name']).first()
        if not existing:
            category = Category(**cat_data)
            db.session.add(category)
    
    # Departments
    departments = [
        {'departmentName': 'Production'},
        {'departmentName': 'Filling'},
        {'departmentName': 'Packing'},
        {'departmentName': 'Quality Control'}
    ]
    
    for dept_data in departments:
        existing = Department.query.filter_by(departmentName=dept_data['departmentName']).first()
        if not existing:
            department = Department(**dept_data)
            db.session.add(department)
    
    # Units of Measure
    uoms = [
        {'uom_name': 'KG', 'description': 'Kilograms'},
        {'uom_name': 'G', 'description': 'Grams'},
        {'uom_name': 'L', 'description': 'Liters'},
        {'uom_name': 'ML', 'description': 'Milliliters'},
        {'uom_name': 'PCS', 'description': 'Pieces'},
        {'uom_name': 'PKT', 'description': 'Packet'}
    ]
    
    for uom_data in uoms:
        existing = UOM.query.filter_by(uom_name=uom_data['uom_name']).first()
        if not existing:
            uom = UOM(**uom_data)
            db.session.add(uom)
    
    db.session.commit()
    print("✅ Lookup tables seeded successfully")

def seed_raw_materials():
    """Create raw material items"""
    print("Seeding raw materials...")
    
    rm_type = ItemType.query.filter_by(type_name='RM').first()
    meat_category = Category.query.filter_by(name='Meat Products').first()
    seasoning_category = Category.query.filter_by(name='Seasonings').first()
    additive_category = Category.query.filter_by(name='Additives').first()
    kg_uom = UOM.query.filter_by(uom_name='KG').first()
    g_uom = UOM.query.filter_by(uom_name='G').first()
    
    raw_materials = [
        {
            'item_code': 'RM-PORK-001',
            'description': 'Pork Shoulder',
            'item_type_id': rm_type.id,
            'category_id': meat_category.id,
            'uom_id': kg_uom.id,
            'price_per_kg': 8.50,
            'min_stock': 100.0,
            'max_stock': 500.0
        },
        {
            'item_code': 'RM-WATER-001',
            'description': 'Filtered Water',
            'item_type_id': rm_type.id,
            'uom_id': kg_uom.id,
            'price_per_kg': 0.01,
            'min_stock': 1000.0,
            'max_stock': 5000.0
        },
        {
            'item_code': 'RM-SALT-001',
            'description': 'Sea Salt',
            'item_type_id': rm_type.id,
            'category_id': seasoning_category.id,
            'uom_id': kg_uom.id,
            'price_per_kg': 2.50,
            'min_stock': 25.0,
            'max_stock': 100.0
        },
        {
            'item_code': 'RM-SPICE-001',
            'description': 'Schiadit Seasoning',
            'item_type_id': rm_type.id,
            'category_id': seasoning_category.id,
            'uom_id': kg_uom.id,
            'price_per_kg': 15.00,
            'min_stock': 10.0,
            'max_stock': 50.0
        },
        {
            'item_code': 'RM-MSG-001',
            'description': 'Monosodium Glutamate',
            'item_type_id': rm_type.id,
            'category_id': additive_category.id,
            'uom_id': g_uom.id,
            'price_per_kg': 8.00,
            'min_stock': 5.0,
            'max_stock': 25.0
        }
    ]
    
    for rm_data in raw_materials:
        existing = ItemMaster.find_by_code_and_description(rm_data['item_code'], rm_data['description'])
        if not existing:
            rm_item = ItemMaster(**rm_data)
            db.session.add(rm_item)
    
    db.session.commit()
    print("✅ Raw materials seeded successfully")

def seed_wip_items():
    """Create WIP items including the 1007 variants"""
    print("Seeding WIP items with composite key examples...")
    
    wip_type = ItemType.query.filter_by(type_name='WIP').first()
    meat_category = Category.query.filter_by(name='Meat Products').first()
    production_dept = Department.query.filter_by(departmentName='Production').first()
    kg_uom = UOM.query.filter_by(uom_name='KG').first()
    
    # The key examples demonstrating composite key functionality
    wip_items = [
        {
            'item_code': '1007',
            'description': 'HF Pulled pork - WIP',
            'item_type_id': wip_type.id,
            'category_id': meat_category.id,
            'department_id': production_dept.department_id,
            'uom_id': kg_uom.id,
            'min_stock': 50.0,
            'max_stock': 200.0,
            'loss_percentage': 5.0,
            'calculation_factor': 0.95
        },
        {
            'item_code': '1007',
            'description': 'GB Pulled Pork - WIP',
            'item_type_id': wip_type.id,
            'category_id': meat_category.id,
            'department_id': production_dept.department_id,
            'uom_id': kg_uom.id,
            'min_stock': 50.0,
            'max_stock': 200.0,
            'loss_percentage': 4.5,
            'calculation_factor': 0.955
        },
        {
            'item_code': '1008',
            'description': 'Ham Base - WIP',
            'item_type_id': wip_type.id,
            'category_id': meat_category.id,
            'department_id': production_dept.department_id,
            'uom_id': kg_uom.id,
            'min_stock': 30.0,
            'max_stock': 150.0,
            'loss_percentage': 3.0,
            'calculation_factor': 0.97
        }
    ]
    
    for wip_data in wip_items:
        existing = ItemMaster.find_by_code_and_description(wip_data['item_code'], wip_data['description'])
        if not existing:
            wip_item = ItemMaster(**wip_data)
            db.session.add(wip_item)
            print(f"  → Created WIP: {wip_data['item_code']} - {wip_data['description']}")
        else:
            print(f"  ✓ WIP already exists: {wip_data['item_code']} - {wip_data['description']}")
    
    db.session.commit()
    print("✅ WIP items seeded successfully")

def seed_recipes():
    """Create recipes for the WIP items"""
    print("Seeding recipes...")
    
    # Get WIP items
    hf_pulled_pork = ItemMaster.find_by_code_and_description('1007', 'HF Pulled pork - WIP')
    gb_pulled_pork = ItemMaster.find_by_code_and_description('1007', 'GB Pulled Pork - WIP')
    ham_base = ItemMaster.find_by_code_and_description('1008', 'Ham Base - WIP')
    
    # Get raw materials
    pork_shoulder = ItemMaster.query.filter_by(item_code='RM-PORK-001').first()
    water = ItemMaster.query.filter_by(item_code='RM-WATER-001').first()
    salt = ItemMaster.query.filter_by(item_code='RM-SALT-001').first()
    schiadit = ItemMaster.query.filter_by(item_code='RM-SPICE-001').first()
    msg = ItemMaster.query.filter_by(item_code='RM-MSG-001').first()
    
    recipes = []
    
    # HF Pulled Pork Recipe
    if hf_pulled_pork:
        hf_recipe = [
            {'recipe_wip_id': hf_pulled_pork.id, 'component_item_id': pork_shoulder.id, 'quantity_kg': 100.0, 'sequence_number': 1},
            {'recipe_wip_id': hf_pulled_pork.id, 'component_item_id': water.id, 'quantity_kg': 88.25, 'sequence_number': 2},
            {'recipe_wip_id': hf_pulled_pork.id, 'component_item_id': salt.id, 'quantity_kg': 9.0, 'sequence_number': 3},
            {'recipe_wip_id': hf_pulled_pork.id, 'component_item_id': schiadit.id, 'quantity_kg': 2.5, 'sequence_number': 4},
            {'recipe_wip_id': hf_pulled_pork.id, 'component_item_id': msg.id, 'quantity_kg': 0.25, 'sequence_number': 5}
        ]
        recipes.extend(hf_recipe)
    
    # GB Pulled Pork Recipe (slightly different quantities)
    if gb_pulled_pork:
        gb_recipe = [
            {'recipe_wip_id': gb_pulled_pork.id, 'component_item_id': pork_shoulder.id, 'quantity_kg': 100.0, 'sequence_number': 1},
            {'recipe_wip_id': gb_pulled_pork.id, 'component_item_id': water.id, 'quantity_kg': 85.0, 'sequence_number': 2},
            {'recipe_wip_id': gb_pulled_pork.id, 'component_item_id': salt.id, 'quantity_kg': 10.0, 'sequence_number': 3},
            {'recipe_wip_id': gb_pulled_pork.id, 'component_item_id': schiadit.id, 'quantity_kg': 3.0, 'sequence_number': 4},
            {'recipe_wip_id': gb_pulled_pork.id, 'component_item_id': msg.id, 'quantity_kg': 0.5, 'sequence_number': 5}
        ]
        recipes.extend(gb_recipe)
    
    # Ham Base Recipe
    if ham_base:
        ham_recipe = [
            {'recipe_wip_id': ham_base.id, 'component_item_id': pork_shoulder.id, 'quantity_kg': 120.0, 'sequence_number': 1},
            {'recipe_wip_id': ham_base.id, 'component_item_id': water.id, 'quantity_kg': 50.0, 'sequence_number': 2},
            {'recipe_wip_id': ham_base.id, 'component_item_id': salt.id, 'quantity_kg': 8.0, 'sequence_number': 3},
            {'recipe_wip_id': ham_base.id, 'component_item_id': schiadit.id, 'quantity_kg': 2.0, 'sequence_number': 4}
        ]
        recipes.extend(ham_recipe)
    
    # Create recipe components
    for recipe_data in recipes:
        existing = RecipeMaster.query.filter_by(
            recipe_wip_id=recipe_data['recipe_wip_id'],
            component_item_id=recipe_data['component_item_id']
        ).first()
        
        if not existing:
            recipe_component = RecipeMaster(**recipe_data)
            recipe_component.calculate_percentage()
            db.session.add(recipe_component)
    
    db.session.commit()
    print("✅ Recipes seeded successfully")

def seed_finished_goods():
    """Create some finished goods items to demonstrate the full hierarchy"""
    print("Seeding finished goods...")
    
    fg_type = ItemType.query.filter_by(type_name='FG').first()
    meat_category = Category.query.filter_by(name='Meat Products').first()
    packing_dept = Department.query.filter_by(departmentName='Packing').first()
    pcs_uom = UOM.query.filter_by(uom_name='PCS').first()
    
    # Get WIP items to link to
    hf_pulled_pork = ItemMaster.find_by_code_and_description('1007', 'HF Pulled pork - WIP')
    gb_pulled_pork = ItemMaster.find_by_code_and_description('1007', 'GB Pulled Pork - WIP')
    
    fg_items = [
        {
            'item_code': '1007.200.HF',
            'description': 'HF Pulled Pork 200g Pack',
            'item_type_id': fg_type.id,
            'category_id': meat_category.id,
            'department_id': packing_dept.department_id,
            'uom_id': pcs_uom.id,
            'wip_item_id': hf_pulled_pork.id if hf_pulled_pork else None,
            'price_per_uom': 4.50,
            'min_stock': 100.0,
            'max_stock': 1000.0
        },
        {
            'item_code': '1007.500.GB',
            'description': 'GB Pulled Pork 500g Pack',
            'item_type_id': fg_type.id,
            'category_id': meat_category.id,
            'department_id': packing_dept.department_id,
            'uom_id': pcs_uom.id,
            'wip_item_id': gb_pulled_pork.id if gb_pulled_pork else None,
            'price_per_uom': 8.95,
            'min_stock': 50.0,
            'max_stock': 500.0
        }
    ]
    
    for fg_data in fg_items:
        existing = ItemMaster.find_by_code_and_description(fg_data['item_code'], fg_data['description'])
        if not existing:
            fg_item = ItemMaster(**fg_data)
            db.session.add(fg_item)
            print(f"  → Created FG: {fg_data['item_code']} - {fg_data['description']}")
    
    db.session.commit()
    print("✅ Finished goods seeded successfully")

def main():
    """Main seeding function"""
    print("🌱 Starting database seeding...")
    print("=" * 50)
    
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            
            # Seed data in order
            seed_lookup_tables()
            seed_raw_materials()
            seed_wip_items()
            seed_recipes()
            seed_finished_goods()
            
            print("=" * 50)
            print("🎉 Database seeding completed successfully!")
            print("\n📊 Summary:")
            print(f"   Items created: {ItemMaster.query.count()}")
            print(f"   Recipe components: {RecipeMaster.query.count()}")
            print(f"   Item types: {ItemType.query.count()}")
            print("\n💡 Key examples:")
            print("   - Item code '1007' now has 2 variants (HF and GB)")
            print("   - Each variant has its own recipe with different quantities")
            print("   - Finished goods link to their respective WIP variants")
            print("\n🚀 You can now run 'python app.py' to start the application!")
            
        except Exception as e:
            print(f"❌ Error during seeding: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    main()