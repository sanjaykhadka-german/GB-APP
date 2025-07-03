#!/usr/bin/env python3
"""
Setup Environment Configuration
Creates .env file with database credentials
"""

import os

def create_env_file():
    """Create .env file with database configuration"""
    
    env_content = """# Database Configuration
SQLALCHEMY_DATABASE_URI=mysql+pymysql://root:german@localhost/gbdb

# Flask Application Configuration
SECRET_KEY=your-secret-key-here-change-this-in-production
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("✅ .env file created successfully!")
        print("📁 Location: .env")
        print("🔑 Database: mysql+pymysql://root:german@localhost/gbdb")
        print("\n⚠️  IMPORTANT: Change the SECRET_KEY in production!")
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        print("\n📝 Please manually create a .env file with this content:")
        print(env_content)

if __name__ == "__main__":
    create_env_file() 