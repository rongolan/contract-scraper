"""
User models and authentication utilities for the Contract Scraper application.
"""

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import psycopg2
import psycopg2.extras
import os
from urllib.parse import urlparse

class User(UserMixin):
    """User model for authentication."""
    
    def __init__(self, id, email, password_hash, role='user', business_type=None, 
                 business_name=None, phone=None, city=None, state='Massachusetts',
                 is_active=True, email_verified=False, created_at=None, last_login=None):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.business_type = business_type
        self.business_name = business_name
        self.phone = phone
        self.city = city
        self.state = state
        self._is_active = is_active  # Use underscore to avoid Flask-Login property conflict
        self.email_verified = email_verified
        self.created_at = created_at
        self.last_login = last_login
    
    def get_id(self):
        """Return the user ID as required by Flask-Login."""
        return str(self.id)
    
    def is_active(self):
        """Return True if the user account is active (required by Flask-Login)."""
        return self._is_active
    
    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return True
    
    def is_anonymous(self):
        """Return False as this is not an anonymous user."""
        return False
    
    def is_admin(self):
        """Check if user has admin role."""
        return self.role == 'admin'
    
    def check_password(self, password):
        """Check if provided password matches the user's password."""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update the user's last login timestamp."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s",
                (self.id,)
            )
            conn.commit()
            self.last_login = datetime.utcnow()
        except Exception:
            conn.rollback()
        finally:
            cur.close()
            conn.close()
    
    def to_dict(self):
        """Convert user object to dictionary (excluding password_hash)."""
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'business_type': self.business_type,
            'business_name': self.business_name,
            'phone': self.phone,
            'city': self.city,
            'state': self.state,
            'is_active': self._is_active,
            'email_verified': self.email_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    @staticmethod
    def create(email, password, role='user', business_type=None, business_name=None, 
               phone=None, city=None, state='Massachusetts'):
        """Create a new user."""
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            # Check if user already exists
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                raise ValueError("User with this email already exists")
            
            # Hash the password
            password_hash = generate_password_hash(password)
            
            # Insert new user
            cur.execute("""
                INSERT INTO users (email, password_hash, role, business_type, business_name, 
                                 phone, city, state, created_at, last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING id, created_at
            """, (email, password_hash, role, business_type, business_name, phone, city, state))
            
            result = cur.fetchone()
            user_id = result['id']
            created_at = result['created_at']
            
            # Create default user preferences
            cur.execute("""
                INSERT INTO user_preferences (user_id, preferred_cities, preferred_industries,
                                            email_notifications, notification_frequency, urgency_alerts)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, [], [], True, 'daily', True))
            
            conn.commit()
            
            # Return the new user object
            return User(
                id=user_id,
                email=email,
                password_hash=password_hash,
                role=role,
                business_type=business_type,
                business_name=business_name,
                phone=phone,
                city=city,
                state=state,
                created_at=created_at
            )
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def get(user_id):
        """Get user by ID."""
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                SELECT id, email, password_hash, role, business_type, business_name,
                       phone, city, state, is_active, email_verified, created_at, last_login
                FROM users WHERE id = %s AND is_active = true
            """, (user_id,))
            
            row = cur.fetchone()
            if row:
                return User(**row)
            return None
            
        except Exception:
            return None
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def get_by_email(email):
        """Get user by email."""
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                SELECT id, email, password_hash, role, business_type, business_name,
                       phone, city, state, is_active, email_verified, created_at, last_login
                FROM users WHERE email = %s AND is_active = true
            """, (email,))
            
            row = cur.fetchone()
            if row:
                return User(**row)
            return None
            
        except Exception:
            return None
        finally:
            cur.close()
            conn.close()
    
    def get_preferences(self):
        """Get user preferences."""
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                SELECT preferred_cities, preferred_industries, min_contract_value,
                       max_contract_value, email_notifications, notification_frequency,
                       urgency_alerts, created_at, updated_at
                FROM user_preferences WHERE user_id = %s
            """, (self.id,))
            
            return cur.fetchone()
            
        except Exception:
            return None
        finally:
            cur.close()
            conn.close()
    
    def update_preferences(self, preferred_cities=None, preferred_industries=None,
                          min_contract_value=None, max_contract_value=None,
                          email_notifications=None, notification_frequency=None,
                          urgency_alerts=None):
        """Update user preferences."""
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                UPDATE user_preferences 
                SET preferred_cities = COALESCE(%s, preferred_cities),
                    preferred_industries = COALESCE(%s, preferred_industries),
                    min_contract_value = COALESCE(%s, min_contract_value),
                    max_contract_value = COALESCE(%s, max_contract_value),
                    email_notifications = COALESCE(%s, email_notifications),
                    notification_frequency = COALESCE(%s, notification_frequency),
                    urgency_alerts = COALESCE(%s, urgency_alerts),
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
            """, (preferred_cities, preferred_industries, min_contract_value,
                  max_contract_value, email_notifications, notification_frequency,
                  urgency_alerts, self.id))
            
            conn.commit()
            return True
            
        except Exception:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()


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


def validate_email(email):
    """Basic email validation."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """Validate password strength."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    
    return True, "Password is valid"


def get_business_types():
    """Get list of available business types."""
    return [
        'Landscaping',
        'Construction',
        'Plumbing',
        'Electrical',
        'HVAC',
        'Cleaning Services',
        'Security Services',
        'IT Services',
        'Consulting',
        'Engineering',
        'Architecture',
        'Transportation',
        'Food Services',
        'Professional Services',
        'Other'
    ]