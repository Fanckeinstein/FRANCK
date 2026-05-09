import os
import sys

# Add parent directory to path so we can import app module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from models import User

# Create the Flask app
app = create_app()

# Initialize database with test users on first run (Vercel serverless)
def init_test_users():
    """Seed database with test users if they don't exist (idempotent)."""
    try:
        with app.app_context():
            # Ensure tables exist
            db.create_all()
            
            # Check if users already exist
            if db.session.query(User).first():
                return
            
            # Create test users
            users_data = [
                {'username': 'president1', 'full_name': 'Jean Dupont', 'email': 'president@unissonslamain.local', 'phone': '+250789123456', 'role': 'president'},
                {'username': 'tresorier1', 'full_name': 'Marie Traore', 'email': 'tresorier@unissonslamain.local', 'phone': '+250789123457', 'role': 'tresorier'},
                {'username': 'secretaire1', 'full_name': 'Sophie Bernard', 'email': 'secretaire@unissonslamain.local', 'phone': '+250789123458', 'role': 'secretaire'},
                {'username': 'member1', 'full_name': 'Pierre Martin', 'email': 'member1@unissonslamain.local', 'phone': '+250789123459', 'role': 'member'},
                {'username': 'member2', 'full_name': 'Alice Johnson', 'email': 'member2@unissonslamain.local', 'phone': '+250789123460', 'role': 'member'},
                {'username': 'member3', 'full_name': 'Bob Leblanc', 'email': 'member3@unissonslamain.local', 'phone': '+250789123461', 'role': 'member'}
            ]
            
            for user_data in users_data:
                user = User(**user_data, is_active=True)
                user.set_password('password123')
                db.session.add(user)
            
            db.session.commit()
            print("✓ Test users initialized in Vercel serverless environment")
    except Exception as e:
        print(f"⚠️  Could not initialize test users: {e}")
        pass

# Initialize on module load for serverless environment
init_test_users()
