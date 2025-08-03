#!/usr/bin/env python3
"""
Database migration script to create authentication tables.
Run this script to add user authentication tables to the existing database.
"""

import psycopg2
import psycopg2.extras
import os
from urllib.parse import urlparse
from datetime import datetime

def get_db_connection():
    """Get database connection using environment variables or local config."""
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Production: Parse DATABASE_URL
        url = urlparse(database_url)
        return psycopg2.connect(
            host=url.hostname,
            database=url.path[1:],  # Remove leading slash
            user=url.username,
            password=url.password,
            port=url.port,
            cursor_factory=psycopg2.extras.RealDictCursor
        )
    else:
        # Development: Use local database
        return psycopg2.connect(
            host="localhost",
            database="contracts",
            user="scraper",
            password="scraperpass",
            cursor_factory=psycopg2.extras.RealDictCursor
        )

def create_auth_tables():
    """Create authentication-related tables."""
    
    # SQL to create users table
    create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('user', 'admin')),
        business_type VARCHAR(100),
        business_name VARCHAR(255),
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
    
    # SQL to create user preferences table
    create_user_preferences_table = """
    CREATE TABLE IF NOT EXISTS user_preferences (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        preferred_cities TEXT[], -- Array of city names
        preferred_industries TEXT[], -- Array of industry names
        min_contract_value DECIMAL(15,2),
        max_contract_value DECIMAL(15,2),
        email_notifications BOOLEAN DEFAULT true,
        notification_frequency VARCHAR(20) DEFAULT 'daily' CHECK (notification_frequency IN ('immediate', 'daily', 'weekly', 'never')),
        urgency_alerts BOOLEAN DEFAULT true,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # SQL to create user sessions table for better session management
    create_user_sessions_table = """
    CREATE TABLE IF NOT EXISTS user_sessions (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        session_token VARCHAR(255) UNIQUE NOT NULL,
        ip_address INET,
        user_agent TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        is_active BOOLEAN DEFAULT true
    );
    """
    
    # SQL to create indexes for better performance
    create_indexes = [
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
        "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);",
        "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);",
        "CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);"
    ]
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        print("Creating authentication tables...")
        
        # Create tables
        cur.execute(create_users_table)
        print("  ✓ Created users table")
        
        cur.execute(create_user_preferences_table)
        print("  ✓ Created user_preferences table")
        
        cur.execute(create_user_sessions_table)
        print("  ✓ Created user_sessions table")
        
        # Create indexes
        for index_sql in create_indexes:
            cur.execute(index_sql)
        print("  ✓ Created database indexes")
        
        # Create a default admin user (optional)
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@contractportal.com')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123!')  # Change in production!
        
        # Check if admin user already exists
        cur.execute("SELECT id FROM users WHERE email = %s", (admin_email,))
        if not cur.fetchone():
            from werkzeug.security import generate_password_hash
            password_hash = generate_password_hash(admin_password)
            
            cur.execute("""
                INSERT INTO users (email, password_hash, role, business_name, is_active, email_verified)
                VALUES (%s, %s, 'admin', 'System Administrator', true, true)
            """, (admin_email, password_hash))
            print(f"  ✓ Created default admin user: {admin_email}")
            print(f"    Default password: {admin_password} (CHANGE THIS IN PRODUCTION!)")
        else:
            print("  ✓ Admin user already exists")
        
        # Commit all changes
        conn.commit()
        print("\n✅ Authentication tables created successfully!")
        
        # Display table information
        cur.execute("""
            SELECT table_name, 
                   (SELECT COUNT(*) FROM information_schema.columns 
                    WHERE table_name = t.table_name AND table_schema = 'public') as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public' 
            AND table_name IN ('users', 'user_preferences', 'user_sessions')
            ORDER BY table_name;
        """)
        
        tables = cur.fetchall()
        print("\nCreated tables:")
        for table in tables:
            print(f"  - {table['table_name']} ({table['column_count']} columns)")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error creating authentication tables: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        raise

if __name__ == "__main__":
    create_auth_tables()