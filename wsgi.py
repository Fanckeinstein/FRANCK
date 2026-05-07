import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set environment to production if not already set
if 'FLASK_ENV' not in os.environ:
    os.environ['FLASK_ENV'] = 'production'

if 'DEBUG' not in os.environ:
    os.environ['DEBUG'] = 'False'

from app import create_app

# Create the application
app = create_app()

if __name__ == '__main__':
    app.run()
