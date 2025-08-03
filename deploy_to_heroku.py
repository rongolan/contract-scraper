#!/usr/bin/env python3
"""
Heroku deployment script for the Contract Scraper authentication system.
This script should be run as a one-time migration command on Heroku.
"""

import os
import sys
from models import get_db_connection

def setup_heroku_database():
    """Set up the database schema on Heroku."""
    
    # Ensure we're using the production database
    if not os.getenv('DATABASE_URL'):
        print("❌ DATABASE_URL not found. This script should run on Heroku.")
        return False
    
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
    
    # SQL to create user_sessions table
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
    
    # SQL to create indexes
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
            print("Creating admin user (golansron@gmail.com)...")
            from werkzeug.security import generate_password_hash
            
            # Create admin user with secure password
            admin_password = "SecureAdmin2025!"  # User should change this
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
            print("✅ Admin user created!")
            print(f"   Email: golansron@gmail.com")
            print(f"   Password: {admin_password}")
            print("   ⚠️  Change this password after first login!")
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

def main():
    """Main function for Heroku deployment."""
    print("🚀 Setting up authentication database on Heroku...")
    print("=" * 50)
    
    if setup_heroku_database():
        print("\n🎉 Heroku database setup completed!")
    else:
        print("\n❌ Heroku database setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()