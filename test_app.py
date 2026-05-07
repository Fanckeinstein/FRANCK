import os
import pytest
from app import create_app
from extensions import db
from models import User, Contribution, Loan

@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Flask test client"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Flask CLI runner"""
    return app.test_cli_runner()

def test_home_page(client):
    """Test home page"""
    response = client.get('/')
    assert response.status_code == 302  # Redirect to login if not authenticated

def test_register(client):
    """Test user registration"""
    response = client.post('/auth/register', data={
        'username': 'testuser',
        'full_name': 'Test User',
        'email': 'test@example.com',
        'phone': '+250789123456',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    
    # Check user was created
    user = User.query.filter_by(username='testuser').first()
    assert user is not None
    assert user.full_name == 'Test User'

def test_login_logout(client, app):
    """Test login and logout"""
    with app.app_context():
        # Create test user
        user = User(
            username='testuser',
            full_name='Test User',
            email='test@example.com',
            role='member',
            is_active=True
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
    
    # Test login
    response = client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'password123'
    })
    assert response.status_code in [200, 302]
    
    # Test logout
    response = client.post('/auth/logout', follow_redirects=True)
    assert response.status_code == 200

def test_member_dashboard(client, app):
    """Test member dashboard access"""
    with app.app_context():
        # Create member user
        user = User(
            username='member1',
            full_name='Member One',
            email='member1@example.com',
            role='member',
            is_active=True
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
    
    # Login
    client.post('/auth/login', data={
        'username': 'member1',
        'password': 'password123'
    })
    
    # Access dashboard
    response = client.get('/member/dashboard')
    assert response.status_code == 200

def test_request_loan(client, app):
    """Test loan request"""
    with app.app_context():
        # Create member
        user = User(
            username='member1',
            full_name='Member One',
            email='member1@example.com',
            role='member',
            is_active=True
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
    
    # Login
    client.post('/auth/login', data={
        'username': 'member1',
        'password': 'password123'
    })
    
    # Request loan
    response = client.post('/member/request-loan', json={
        'amount': 50000,
        'reason': 'Emergency'
    }, follow_redirects=True)
    assert response.status_code == 200

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
