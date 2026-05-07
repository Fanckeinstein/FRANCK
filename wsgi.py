import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure production settings
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('DEBUG', 'False')

from app import create_app

# Create and configure the WSGI application
app = create_app()

# Gunicorn will use this app variable
if __name__ == '__main__':
    # This is for local testing only
    # In production, Gunicorn will call app directly
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
