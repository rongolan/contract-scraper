# Contract Scraper Authentication System

## Overview

The Contract Scraper now includes a comprehensive user authentication system with role-based access control, user preferences, and admin functionality.

## Features

### Authentication Features
- ✅ User registration with email/password
- ✅ Secure login with session management
- ✅ Password hashing with Werkzeug
- ✅ Role-based permissions (user/admin)
- ✅ Session-based authentication
- ✅ Password strength validation

### User Management
- ✅ User profiles with business information
- ✅ User preferences (cities, industries, notifications)
- ✅ Admin panel for system management
- ✅ Default admin user: `golansron@gmail.com`

### Route Protection
- **Public routes**: `/`, `/contracts`, `/login`, `/signup`
- **Auth required**: `/home`, `/profile`, `/settings`
- **Admin only**: `/admin`
- **Root route logic**: Redirects to `/home` if logged in, shows landing page if not

## Database Schema

### Users Table
```sql
CREATE TABLE users (
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
```

### User Preferences Table
```sql
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    preferred_cities TEXT[] DEFAULT '{}',
    preferred_industries TEXT[] DEFAULT '{}',
    min_contract_value DECIMAL(12,2),
    max_contract_value DECIMAL(12,2),
    email_notifications BOOLEAN DEFAULT true,
    notification_frequency VARCHAR(20) DEFAULT 'daily',
    urgency_alerts BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);
```

### User Sessions Table
```sql
CREATE TABLE user_sessions (
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
```

## Setup Instructions

### Local Development

1. **Set up the database schema:**
   ```bash
   python setup_database.py
   ```

2. **Start the Flask application:**
   ```bash
   python app.py
   ```

3. **Access the application:**
   - Visit: http://localhost:5001
   - Admin login: `golansron@gmail.com` / `AdminPass123!`

### Heroku Deployment

1. **Set up environment variables on Heroku:**
   ```bash
   heroku config:set SECRET_KEY=your-secret-key-here
   heroku config:set DATABASE_URL=your-postgres-url
   ```

2. **Run the database setup on Heroku:**
   ```bash
   heroku run python deploy_to_heroku.py
   ```

3. **Deploy the application:**
   ```bash
   git push heroku main
   ```

## API Endpoints

### Authentication APIs
- `POST /login` - User login
- `POST /signup` - User registration
- `GET /logout` - User logout

### User Management APIs
- `GET /api/user/profile` - Get current user profile
- `POST /api/user/preferences` - Update user preferences
- `GET /api/business-types` - Get available business types

### Contract APIs (existing)
- `GET /api/contracts` - Get all contracts
- `GET /api/filters` - Get filter options

## Security Features

### Password Requirements
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number

### Session Management
- Secure session cookies
- Session timeout
- Remember me functionality
- IP and user agent tracking (optional)

### Role-Based Access Control
- **User role**: Access to personal dashboard, contracts, profile
- **Admin role**: Full system access including admin panel

## Admin User

A default admin user is created during setup:
- **Email**: `golansron@gmail.com`
- **Initial Password**: `AdminPass123!` (local) / `SecureAdmin2025!` (Heroku)
- **Role**: admin
- **⚠️ IMPORTANT**: Change the password immediately after first login

## File Structure

### Backend Files
- `app.py` - Main Flask application with authentication routes
- `models.py` - User model and database utilities
- `setup_database.py` - Local database setup script
- `deploy_to_heroku.py` - Heroku database setup script

### Frontend Integration
- `templates/index.html` - Single-page application with authentication UI
- Client-side routing with authentication state management
- Login/signup forms with validation
- User profile and preferences interface

## Environment Variables

Required environment variables:

```env
# Database
DATABASE_URL=postgresql://username:password@host:port/database

# Authentication
SECRET_KEY=your-secret-key-here-change-in-production

# Google Sheets (existing)
GOOGLE_SHEETS_CREDENTIALS_JSON={"type": "service_account", ...}

# Application
FLASK_ENV=production
PORT=5000
```

## Testing

### Local Testing
1. Run `python setup_database.py` to set up the database
2. Start the app with `python app.py`
3. Test user registration at `/signup`
4. Test user login at `/login`
5. Test admin access with `golansron@gmail.com`

### Production Testing
1. Deploy to Heroku
2. Run `heroku run python deploy_to_heroku.py`
3. Test the live application
4. Verify admin access works

## Next Steps

1. **User Testing**: Show the authentication system to service business owners
2. **UI Enhancements**: Improve user onboarding and profile management
3. **Email Notifications**: Implement contract alert system
4. **Admin Panel**: Add contract management features for admin users
5. **User Analytics**: Track user engagement and preferences

## Troubleshooting

### Common Issues

1. **Database Connection Error**:
   - Check `DATABASE_URL` environment variable
   - Verify PostgreSQL is running (local) or accessible (Heroku)

2. **Authentication Not Working**:
   - Check `SECRET_KEY` is set
   - Verify user tables exist in database
   - Check Flask-Login configuration

3. **Admin User Not Found**:
   - Run the setup script again
   - Check if user was created in database
   - Verify email address is correct

### Debug Commands

```bash
# Check database tables
heroku pg:psql -c "\dt"

# Check admin user
heroku pg:psql -c "SELECT email, role FROM users WHERE role = 'admin';"

# Check application logs
heroku logs --tail
```