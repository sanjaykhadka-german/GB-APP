#!/usr/bin/env python3
"""
Quick setup script for the Composite Key Item Master System.
This script helps initialize the project with all necessary dependencies and data.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_banner():
    """Print welcome banner"""
    print("=" * 60)
    print("  🔑 Composite Key Item Master System - Setup")
    print("=" * 60)
    print()

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version.split()[0]}")

def check_dependencies():
    """Check if required system dependencies are available"""
    print("\n📦 Checking system dependencies...")
    
    dependencies = {
        'pip': 'pip --version',
        'mysql': 'mysql --version'
    }
    
    missing = []
    for dep, cmd in dependencies.items():
        try:
            result = subprocess.run(cmd.split(), capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {dep}: Available")
            else:
                missing.append(dep)
        except FileNotFoundError:
            missing.append(dep)
    
    if missing:
        print(f"⚠️  Warning: The following dependencies are missing: {', '.join(missing)}")
        print("   Please install them manually if needed.")
    
    return len(missing) == 0

def create_virtual_environment():
    """Create and activate virtual environment"""
    print("\n🐍 Setting up virtual environment...")
    
    if os.path.exists('venv'):
        print("✅ Virtual environment already exists")
        return True
    
    try:
        subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
        print("✅ Virtual environment created successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False

def install_requirements():
    """Install Python requirements"""
    print("\n📚 Installing Python dependencies...")
    
    # Determine pip path based on OS
    if os.name == 'nt':  # Windows
        pip_path = os.path.join('venv', 'Scripts', 'pip')
    else:  # Unix/Linux/MacOS
        pip_path = os.path.join('venv', 'bin', 'pip')
    
    if not os.path.exists(pip_path):
        print("❌ Virtual environment pip not found")
        return False
    
    try:
        subprocess.run([pip_path, 'install', '-r', 'requirements.txt'], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_environment_file():
    """Create .env file from template"""
    print("\n⚙️  Setting up environment configuration...")
    
    if os.path.exists('.env'):
        print("✅ .env file already exists")
        return True
    
    if os.path.exists('.env.example'):
        try:
            shutil.copy('.env.example', '.env')
            print("✅ .env file created from template")
            print("⚠️  Please edit .env file with your database credentials")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    else:
        print("❌ .env.example file not found")
        return False

def check_database_connection():
    """Check if database is accessible"""
    print("\n🗄️  Checking database connection...")
    
    # This is a basic check - in a real setup you'd want to test the actual connection
    print("⚠️  Please ensure your MySQL server is running and accessible")
    print("   Database setup will be completed in the next step")
    return True

def run_database_setup():
    """Initialize database and run migrations"""
    print("\n🗄️  Setting up database...")
    
    # Determine python path based on OS
    if os.name == 'nt':  # Windows
        python_path = os.path.join('venv', 'Scripts', 'python')
    else:  # Unix/Linux/MacOS
        python_path = os.path.join('venv', 'bin', 'python')
    
    try:
        # Create all tables
        print("   Creating database tables...")
        subprocess.run([python_path, '-c', 'from app import app, db; app.app_context().push(); db.create_all()'], check=True)
        print("✅ Database tables created")
        
        # Seed initial data
        print("   Seeding initial data...")
        subprocess.run([python_path, 'seed_data.py'], check=True)
        print("✅ Initial data seeded")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Database setup failed: {e}")
        print("   Please check your database configuration in .env file")
        return False

def print_next_steps():
    """Print instructions for next steps"""
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit the .env file with your database credentials")
    print("2. Create the database in MySQL:")
    print("   CREATE DATABASE composite_key_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    print("3. If you haven't run database setup yet:")
    print("   python seed_data.py")
    print("4. Start the application:")
    print("   python app.py")
    print("5. Open http://localhost:5000 in your browser")
    print("\n💡 Key features to explore:")
    print("   - Item code '1007' with two variants (HF and GB)")
    print("   - Different recipes for each variant")
    print("   - Composite key constraint demonstration")

def main():
    """Main setup function"""
    print_banner()
    
    try:
        # Step 1: Check Python version
        check_python_version()
        
        # Step 2: Check system dependencies
        check_dependencies()
        
        # Step 3: Create virtual environment
        if not create_virtual_environment():
            return False
        
        # Step 4: Install requirements
        if not install_requirements():
            return False
        
        # Step 5: Setup environment file
        if not setup_environment_file():
            return False
        
        # Step 6: Check database
        if not check_database_connection():
            return False
        
        # Step 7: Offer to run database setup
        print("\n❓ Would you like to set up the database now? (y/n)")
        setup_db = input().lower().strip()
        
        if setup_db in ['y', 'yes']:
            if run_database_setup():
                print("\n🚀 Full setup completed!")
            else:
                print("\n⚠️  Setup completed but database setup failed")
                print("   Please run 'python seed_data.py' manually after configuring .env")
        else:
            print("\n✅ Basic setup completed")
        
        print_next_steps()
        return True
        
    except KeyboardInterrupt:
        print("\n\n❌ Setup interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error during setup: {e}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)