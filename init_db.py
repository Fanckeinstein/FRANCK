#!/usr/bin/env python3
"""
Script to initialize the database with sample data
"""
import os
import sys
from app import create_app
from extensions import db
from models import User, Contribution, Loan, Transaction
from datetime import datetime, timedelta

def init_db():
    """Initialize the database with sample data"""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✓ Database tables created")
        
        # Check if users already exist
        if db.session.query(User).first():
            print("✓ Database already initialized with users")
            return
        
        # Create sample users
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
        print(f"✓ Created {len(users)} users")
        
        # Create sample contributions for current month
        current_month = datetime.utcnow().strftime('%Y-%m')
        for i, member in enumerate(users[3:]):  # Members only
            contribution = Contribution(
                user_id=member.id,
                amount=1000.0,
                month=current_month,
                status='paid' if i % 2 == 0 else 'pending',
                payment_method='mobile_money' if i % 2 == 0 else None,
                paid_at=datetime.utcnow() if i % 2 == 0 else None,
                validated_by=users[1].id if i % 2 == 0 else None
            )
            db.session.add(contribution)
        
        # Create previous month contributions
        prev_month = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m')
        for member in users[3:]:
            contribution = Contribution(
                user_id=member.id,
                amount=1000.0,
                month=prev_month,
                status='paid',
                payment_method='cash',
                paid_at=datetime.utcnow() - timedelta(days=30),
                validated_by=users[1].id
            )
            db.session.add(contribution)
        
        db.session.commit()
        print("✓ Created sample contributions")
        
        # Create sample loans
        loan1 = Loan(
            user_id=users[3].id,
            amount=50000.0,
            reason='Emergency medical expenses for family member',
            status='pending',
            requested_at=datetime.utcnow()
        )
        
        loan2 = Loan(
            user_id=users[4].id,
            amount=30000.0,
            reason='Car repair needed urgently',
            status='approved',
            requested_at=datetime.utcnow() - timedelta(days=5),
            approved_at=datetime.utcnow() - timedelta(days=4),
            approved_by=users[0].id,
            approval_notes='Approved - Good standing member',
            repayment_deadline=datetime.utcnow() + timedelta(days=30)
        )
        
        db.session.add(loan1)
        db.session.add(loan2)
        db.session.commit()
        print("✓ Created sample loans")
        
        # Create sample transactions
        transactions = [
            Transaction(
                type='contribution_paid',
                user_id=users[3].id,
                amount=1000.0,
                description=f'Contribution {current_month}',
                reference_id=1
            ),
            Transaction(
                type='loan_requested',
                user_id=users[4].id,
                amount=30000.0,
                description='Emergency car repair',
                reference_id=2
            ),
        ]
        
        for t in transactions:
            db.session.add(t)
        
        db.session.commit()
        print("✓ Created sample transactions")
        
        print("\n" + "="*50)
        print("Database initialization complete!")
        print("="*50)
        print("\nSample users created:")
        print("  - president1 / password123 (Président)")
        print("  - tresorier1 / password123 (Trésorier)")
        print("  - secretaire1 / password123 (Secrétaire)")
        print("  - member1 / password123 (Membre)")
        print("  - member2 / password123 (Membre)")
        print("  - member3 / password123 (Membre)")
        print("\nYou can now run the application with:")
        print("  python app.py")


if __name__ == '__main__':
    init_db()
