from flask import Flask, jsonify, render_template
from flask_cors import CORS
import psycopg2
import psycopg2.extras
from datetime import datetime
import os
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Database connection
def get_db_connection():
    # Use DATABASE_URL environment variable for production, fallback to local for development
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

@app.route('/')
def index():
    """Serve the main UI"""
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

if __name__ == '__main__':
    # Get port from environment variable for Heroku, default to 5001 for local development
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)