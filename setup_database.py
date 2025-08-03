#!/usr/bin/env python3
"""
Database setup script for the Contract Scraper authentication system.
This script creates the necessary tables for user authentication and preferences.
"""

import os
import sys
from models import get_db_connection

def create_database_schema():
    """Create the database schema for user authentication."""
    
    # SQL to create users table
    create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('user', 'admin')),
        business_name VARCHAR(255),
        business_type VARCHAR(100),
        phone VARCHAR(20),
        city VARCHAR(100),
        state VARCHAR(50) DEFAULT 'Massachusetts',
        is_active BOOLEAN DEFAULT true,
        email_verified BOOLEAN DEFAULT false,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # SQL to create user_preferences table
    create_preferences_table = """
    CREATE TABLE IF NOT EXISTS user_preferences (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        preferred_cities TEXT[] DEFAULT '{}',
        preferred_industries TEXT[] DEFAULT '{}',
        min_contract_value DECIMAL(12,2),
        max_contract_value DECIMAL(12,2),
        email_notifications BOOLEAN DEFAULT true,
        notification_frequency VARCHAR(20) DEFAULT 'daily' CHECK (notification_frequency IN ('immediate', 'daily', 'weekly', 'never')),
        urgency_alerts BOOLEAN DEFAULT true,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id)
    );
    """
    
    # SQL to create user_sessions table (optional for advanced session management)
    create_sessions_table = """
    CREATE TABLE IF NOT EXISTS user_sessions (
        id SERIAL PRIMARY KEY,
        session_id VARCHAR(255) UNIQUE NOT NULL,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        ip_address INET,
        user_agent TEXT,
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP
    );
    """
    
    # SQL to create indexes for better performance
    create_indexes = """
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
    CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_active ON user_sessions(is_active);
    CREATE INDEX IF NOT EXISTS idx_preferences_user_id ON user_preferences(user_id);
    """
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        print("Creating users table...")
        cur.execute(create_users_table)
        
        print("Creating user_preferences table...")
        cur.execute(create_preferences_table)
        
        print("Creating user_sessions table...")
        cur.execute(create_sessions_table)
        
        print("Creating database indexes...")
        cur.execute(create_indexes)
        
        conn.commit()
        print("✅ Database schema created successfully!")
        
        # Check if admin user exists
        cur.execute("SELECT id FROM users WHERE email = %s", ('golansron@gmail.com',))
        admin_exists = cur.fetchone()
        
        if not admin_exists:
            print("\n🔧 Creating admin user (golansron@gmail.com)...")
            from werkzeug.security import generate_password_hash
            
            # Create admin user with temporary password
            admin_password = "AdminPass123!"  # User should change this immediately
            password_hash = generate_password_hash(admin_password)
            
            cur.execute("""
                INSERT INTO users (email, password_hash, role, business_name, business_type, 
                                 city, state, is_active, email_verified)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, ('golansron@gmail.com', password_hash, 'admin', 'Contract Portal Admin', 
                  'IT Services', 'Boston', 'Massachusetts', True, True))
            
            admin_id = cur.fetchone()['id']
            
            # Create default preferences for admin
            cur.execute("""
                INSERT INTO user_preferences (user_id, preferred_cities, preferred_industries,
                                            email_notifications, notification_frequency, urgency_alerts)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (admin_id, ['Boston', 'Cambridge', 'Somerville'], ['IT Services', 'Consulting'], 
                  True, 'immediate', True))
            
            conn.commit()
            print(f"✅ Admin user created successfully!")
            print(f"   Email: golansron@gmail.com")
            print(f"   Temporary Password: {admin_password}")
            print(f"   ⚠️  IMPORTANT: Change this password immediately after first login!")
        else:
            print("ℹ️  Admin user already exists")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating database schema: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def check_database_connection():
    """Test database connection."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"✅ Database connection successful!")
        if version:
            print(f"   PostgreSQL version: {version['version'] if isinstance(version, dict) else version[0]}")
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def main():
    """Main function to set up the database."""
    print("🚀 Setting up Contract Scraper Authentication Database...")
    print("=" * 60)
    
    # Check database connection first
    if not check_database_connection():
        print("\n❌ Cannot proceed without database connection.")
        print("Please check your DATABASE_URL or local PostgreSQL setup.")
        sys.exit(1)
    
    # Create schema
    if create_database_schema():
        print("\n🎉 Database setup completed successfully!")
        print("\nNext steps:")
        print("1. Start your Flask application: python app.py")
        print("2. Visit http://localhost:5001 (local) or your Heroku URL")
        print("3. Test user registration and login")
        print("4. Login as admin (golansron@gmail.com) and change password")
    else:
        print("\n❌ Database setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()