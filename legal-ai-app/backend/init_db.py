#!/usr/bin/env python3
"""
Database initialization script for Legal AI Assistant.
This script creates the database tables and sets up an initial admin user.
"""

import os
import sys
from sqlalchemy.orm import Session
from passlib.context import CryptContext

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import engine, SessionLocal, Base, User
from config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_database():
    """Initialize the database with tables and admin user."""
    print("🚀 Initializing Legal AI Assistant database...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        
        # Create database session
        db = SessionLocal()
        
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        
        if not admin_user:
            # Create admin user
            admin_password = "admin123"  # Change this in production!
            hashed_password = pwd_context.hash(admin_password)
            
            admin_user = User(
                email="admin@legalai.com",
                username="admin",
                full_name="System Administrator",
                hashed_password=hashed_password,
                is_active=True,
                is_superuser=True
            )
            
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            
            print("✅ Admin user created successfully")
            print(f"   Username: admin")
            print(f"   Password: {admin_password}")
            print("   ⚠️  IMPORTANT: Change this password after first login!")
        else:
            print("ℹ️  Admin user already exists")
        
        # Check if any regular users exist
        regular_users = db.query(User).filter(User.is_superuser == False).count()
        print(f"ℹ️  Regular users in database: {regular_users}")
        
        db.close()
        
        print("🎉 Database initialization completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during database initialization: {e}")
        sys.exit(1)

def create_test_user():
    """Create a test user for development purposes."""
    print("\n🔧 Creating test user...")
    
    try:
        db = SessionLocal()
        
        # Check if test user already exists
        test_user = db.query(User).filter(User.username == "testuser").first()
        
        if not test_user:
            # Create test user
            test_password = "test123"
            hashed_password = pwd_context.hash(test_password)
            
            test_user = User(
                email="test@legalai.com",
                username="testuser",
                full_name="Test User",
                hashed_password=hashed_password,
                is_active=True,
                is_superuser=False
            )
            
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            
            print("✅ Test user created successfully")
            print(f"   Username: testuser")
            print(f"   Password: {test_password}")
        else:
            print("ℹ️  Test user already exists")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")

def show_database_info():
    """Show information about the database."""
    print("\n📊 Database Information:")
    print(f"   Database URL: {settings.database_url}")
    print(f"   Host: {settings.host}")
    print(f"   Port: {settings.port}")
    print(f"   Debug mode: {settings.debug}")

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 Legal AI Assistant - Database Initialization")
    print("=" * 60)
    
    # Show database configuration
    show_database_info()
    
    # Initialize database
    init_database()
    
    # Create test user (optional)
    create_test_user()
    
    print("\n" + "=" * 60)
    print("✅ Setup completed! You can now run the application with:")
    print("   uvicorn main:app --reload")
    print("=" * 60)