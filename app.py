from flask import Flask, jsonify, render_template, redirect, url_for, request, flash, session
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import psycopg2
import psycopg2.extras
from datetime import datetime
import os
from urllib.parse import urlparse
from models import User, get_db_connection, validate_email, validate_password, get_business_types
from werkzeug.security import check_password_hash

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Configure Flask-Login
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.get(int(user_id))

# Database connection function is imported from models.py

@app.route('/')
def index():
    """Serve the main UI - Landing page or redirect authenticated users to home"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/contracts')
def contracts():
    """Serve the contracts page"""
    return render_template('index.html')

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))
        
        if not email or not password:
            flash('Please provide both email and password.', 'error')
            return render_template('index.html')
        
        user = User.get_by_email(email)
        if user and user.check_password(password):
            login_user(user, remember=remember)
            user.update_last_login()
            
            # Redirect to next page or home
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle user registration"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        business_name = request.form.get('business_name', '').strip()
        business_type = request.form.get('business_type', '').strip()
        phone = request.form.get('phone', '').strip()
        city = request.form.get('city', '').strip()
        
        # Validation
        if not email or not password:
            flash('Email and password are required.', 'error')
            return render_template('index.html')
        
        if not validate_email(email):
            flash('Please provide a valid email address.', 'error')
            return render_template('index.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('index.html')
        
        is_valid, message = validate_password(password)
        if not is_valid:
            flash(message, 'error')
            return render_template('index.html')
        
        try:
            user = User.create(
                email=email,
                password=password,
                business_name=business_name,
                business_type=business_type,
                phone=phone,
                city=city
            )
            
            login_user(user)
            flash('Account created successfully! Welcome to Contract Opportunities Portal.', 'success')
            return redirect(url_for('home'))
            
        except ValueError as e:
            flash(str(e), 'error')
        except Exception as e:
            flash('An error occurred while creating your account. Please try again.', 'error')
    
    return render_template('index.html')

@app.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('index.html')

@app.route('/settings')
@login_required
def settings():
    """User settings page"""
    return render_template('index.html')

@app.route('/admin')
@login_required
def admin():
    """Admin panel - restricted to admin users"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/home')
@login_required
def home():
    """Serve the authenticated user's home page with personalized content"""
    return render_template('index.html')

# Catch-all route for unknown paths - redirect to landing page
@app.route('/<path:path>')
def catch_all(path):
    """Handle unknown routes by redirecting to appropriate pages"""
    # If path starts with 'api/', return 404 for API routes
    if path.startswith('api/'):
        return jsonify({'error': 'API endpoint not found'}), 404
    
    # For other unknown paths, serve the main template and let client-side routing handle it
    return render_template('index.html')

@app.route('/api/contracts')
def get_contracts():
    """API endpoint to get all contracts"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get all contracts with formatted data
        cur.execute("""
            SELECT 
                "Title" as title,
                "Department" as department,
                "Industry" as industry,
                "Estimated Value" as estimated_value,
                "Release Date_Display" as release_date,
                "Due Date_Display" as due_date,
                "Instructions" as instructions,
                "City" as city,
                "Source Type" as source_type,
                "Source URL" as source_url,
                "Status" as status
            FROM contract_opportunities
            ORDER BY "Due Date_Display" ASC, "Release Date_Display" DESC
        """)
        
        contracts = cur.fetchall()
        
        # Format the data for frontend
        formatted_contracts = []
        for contract in contracts:
            # Format estimated value
            estimated_value = contract['estimated_value']
            if estimated_value:
                try:
                    value_float = float(estimated_value)
                    if value_float > 0:
                        estimated_value_display = f"${value_float:,.0f}"
                    else:
                        estimated_value_display = "Open Pricing"
                except (ValueError, TypeError):
                    estimated_value_display = "Open Pricing"
            else:
                estimated_value_display = "Open Pricing"
            
            # Format dates for display
            due_date_display = contract['due_date'] if contract['due_date'] else "TBD"
            release_date_display = contract['release_date'] if contract['release_date'] else "TBD"
            
            # Determine urgency (days until due date)
            urgency = "low"
            days_until_due = None
            if contract['due_date'] and contract['due_date'] != "TBD":
                try:
                    # Parse different date formats
                    due_date_str = str(contract['due_date'])
                    if ' ' in due_date_str:  # Has time component
                        due_date = datetime.strptime(due_date_str.split(' ')[0], '%Y-%m-%d')
                    else:  # Date only
                        due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
                    
                    days_until_due = (due_date - datetime.now()).days
                    if days_until_due <= 7:
                        urgency = "high"
                    elif days_until_due <= 30:
                        urgency = "medium"
                except (ValueError, TypeError):
                    pass
            
            formatted_contracts.append({
                'title': contract['title'],
                'department': contract['department'],
                'industry': contract['industry'] or 'Other',
                'estimated_value': estimated_value_display,
                'release_date': release_date_display,
                'due_date': due_date_display,
                'instructions': contract['instructions'],
                'city': contract['city'],
                'source_type': contract['source_type'],
                'source_url': contract['source_url'],
                'status': contract['status'] or 'Open',
                'urgency': urgency,
                'days_until_due': days_until_due
            })
        
        cur.close()
        conn.close()
        
        return jsonify({
            'contracts': formatted_contracts,
            'total': len(formatted_contracts)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/filters')
def get_filters():
    """API endpoint to get available filter options"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get unique industries
        cur.execute('SELECT DISTINCT "Industry" FROM contract_opportunities WHERE "Industry" IS NOT NULL ORDER BY "Industry"')
        industries = [row['Industry'] for row in cur.fetchall()]
        
        # Get unique cities
        cur.execute('SELECT DISTINCT "City" FROM contract_opportunities ORDER BY "City"')
        cities = [row['City'] for row in cur.fetchall()]
        
        # Get unique statuses
        cur.execute('SELECT DISTINCT "Status" FROM contract_opportunities WHERE "Status" IS NOT NULL ORDER BY "Status"')
        statuses = [row['Status'] for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        
        return jsonify({
            'industries': industries,
            'cities': cities,
            'statuses': statuses
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# User Management API Routes
@app.route('/api/user/profile')
@login_required
def api_user_profile():
    """API endpoint to get current user profile"""
    try:
        user_data = current_user.to_dict()
        preferences = current_user.get_preferences()
        
        return jsonify({
            'user': user_data,
            'preferences': dict(preferences) if preferences else None,
            'business_types': get_business_types()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/preferences', methods=['POST'])
@login_required
def api_update_preferences():
    """API endpoint to update user preferences"""
    try:
        data = request.get_json()
        
        result = current_user.update_preferences(
            preferred_cities=data.get('preferred_cities'),
            preferred_industries=data.get('preferred_industries'),
            min_contract_value=data.get('min_contract_value'),
            max_contract_value=data.get('max_contract_value'),
            email_notifications=data.get('email_notifications'),
            notification_frequency=data.get('notification_frequency'),
            urgency_alerts=data.get('urgency_alerts')
        )
        
        if result:
            return jsonify({'success': True, 'message': 'Preferences updated successfully'})
        else:
            return jsonify({'error': 'Failed to update preferences'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/business-types')
def api_business_types():
    """API endpoint to get available business types"""
    return jsonify({'business_types': get_business_types()})

if __name__ == '__main__':
    # Get port from environment variable for Heroku, default to 5001 for local development
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)