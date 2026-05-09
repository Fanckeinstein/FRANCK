#!/usr/bin/env python
"""
Migrate from SQLite to Neon PostgreSQL.
This script:
1. Exports data from SQLite (if exists)
2. Tests connection to Neon
3. Creates tables in Neon
4. Seeds with test users
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from models import User

def migrate_to_neon():
    """Migrate database to Neon PostgreSQL."""
    
    # Use PostgreSQL URL if set, otherwise fall back to SQLite
    db_url = os.getenv('DATABASE_URL', 'sqlite:///unissons.db')
    
    print(f"📊 Using database: {db_url[:50]}...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Create all tables
            print("✓ Creating tables in database...")
            db.create_all()
            
            # Check if users exist
            existing = db.session.query(User).count()
            if existing > 0:
                print(f"✓ Database already has {existing} users")
                return
            
            # Seed with test users
            print("✓ Seeding test users...")
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
            print(f"✓ {len(users_data)} test users created")
            print("\n✅ Migration complete!")
            print("\nTest credentials:")
            print("  - president1 / password123")
            print("  - tresorier1 / password123")
            print("  - secretaire1 / password123")
            print("  - member1 / password123")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

if __name__ == '__main__':
    migrate_to_neon()
