#!/usr/bin/env python3

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from database import db
from models.user import User

def create_users_table():
    """Create the users table and add a default admin user"""
    
    print("Creating users table and default admin user...")
    
    try:
        # Create Flask app context
        app = create_app()
        
        with app.app_context():
            # Create all tables (including users table)
            db.create_all()
            print("✅ Users table created successfully!")
            
            # Check if admin user already exists
            admin_user = User.query.filter_by(username='admin').first()
            
            if not admin_user:
                # Create default admin user
                admin_user = User(
                    username='admin',
                    email='admin@gb-app.com'
                )
                admin_user.set_password('admin123')  # Default password
                
                db.session.add(admin_user)
                db.session.commit()
                
                print("✅ Default admin user created!")
                print("   Username: admin")
                print("   Password: admin123")
                print("   Email: admin@gb-app.com")
                print("\n⚠️  IMPORTANT: Please change the default password after first login!")
            else:
                print("ℹ️  Admin user already exists")
                
            # Display table info
            print("\n📊 Users table structure:")
            print("   - id (Primary Key)")
            print("   - username (Unique)")
            print("   - email (Unique)")
            print("   - password_hash")
            print("   - is_active (Boolean)")
            print("   - created_at (DateTime)")
            print("   - updated_at (DateTime)")
            print("   - last_login (DateTime)")
            
            print("\n✅ Users table setup completed successfully!")
            
    except Exception as e:
        print(f"❌ Error creating users table: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def add_sample_user():
    """Add a sample user for testing"""
    
    try:
        app = create_app()
        
        with app.app_context():
            # Check if test user already exists
            test_user = User.query.filter_by(username='testuser').first()
            
            if not test_user:
                test_user = User(
                    username='testuser',
                    email='test@gb-app.com'
                )
                test_user.set_password('test123')
                
                db.session.add(test_user)
                db.session.commit()
                
                print("✅ Test user created!")
                print("   Username: testuser")
                print("   Password: test123")
                print("   Email: test@gb-app.com")
            else:
                print("ℹ️  Test user already exists")
                
    except Exception as e:
        print(f"❌ Error creating test user: {str(e)}")

if __name__ == "__main__":
    print("🚀 Setting up authentication system...")
    print("=" * 50)
    
    success = create_users_table()
    
    if success:
        print("\n" + "=" * 50)
        print("🎉 Authentication system setup complete!")
        print("\n📝 Next steps:")
        print("1. Run the Flask app: python app.py")
        print("2. Navigate to: http://localhost:5000/login")
        print("3. Login with admin/admin123")
        print("4. Change the default password")
        print("5. Create additional users via /register")
        
        # Ask if user wants to create a test user
        create_test = input("\n❓ Create a test user? (y/n): ").lower().strip()
        if create_test == 'y':
            add_sample_user()
    else:
        print("❌ Setup failed. Please check the errors above.")
        sys.exit(1) 