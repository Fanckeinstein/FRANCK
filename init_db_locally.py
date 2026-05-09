#!/usr/bin/env python
"""Initialize database locally with test users for Vercel deployment."""

import os
import sys

# Ensure we're in the right directory
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from models import User

def init_and_seed():
    """Create database and seed with test users."""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✓ Database tables created")
        
        # Check if users already exist
        existing = db.session.query(User).first()
        if existing:
            print("✓ Database already has users, skipping seed")
            return
        
        # Create test users
        users_data = [
            {
                'username': 'president1',
                'full_name': 'Jean Dupont',
                'email': 'president@unissonslamain.local',
                'phone': '+250789123456',
                'role': 'president'
            },
            {
                'username': 'tresorier1',
                'full_name': 'Marie Traore',
                'email': 'tresorier@unissonslamain.local',
                'phone': '+250789123457',
                'role': 'tresorier'
            },
            {
                'username': 'secretaire1',
                'full_name': 'Sophie Bernard',
                'email': 'secretaire@unissonslamain.local',
                'phone': '+250789123458',
                'role': 'secretaire'
            },
            {
                'username': 'member1',
                'full_name': 'Pierre Martin',
                'email': 'member1@unissonslamain.local',
                'phone': '+250789123459',
                'role': 'member'
            },
            {
                'username': 'member2',
                'full_name': 'Alice Johnson',
                'email': 'member2@unissonslamain.local',
                'phone': '+250789123460',
                'role': 'member'
            },
            {
                'username': 'member3',
                'full_name': 'Bob Leblanc',
                'email': 'member3@unissonslamain.local',
                'phone': '+250789123461',
                'role': 'member'
            }
        ]
        
        users = []
        for user_data in users_data:
            user = User(**user_data, is_active=True)
            user.set_password('password123')
            users.append(user)
            db.session.add(user)
        
        db.session.commit()
        print(f"✓ Database seeded with {len(users)} users")
        print("\n✓ Test credentials:")
        print("  - president1 / password123")
        print("  - tresorier1 / password123")
        print("  - secretaire1 / password123")
        print("  - member1 / password123")
        print("\n✓ Ready for deployment!")

if __name__ == '__main__':
    init_and_seed()
