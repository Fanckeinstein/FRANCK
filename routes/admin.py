from flask import Blueprint, request, jsonify
import os
from sqlalchemy import func

bp = Blueprint('admin', __name__)


@bp.route('/admin/seed', methods=['POST'])
def seed():
    token = os.getenv('SEED_TOKEN')
    header = request.headers.get('X-SEED-TOKEN')
    if not token or header != token:
        return jsonify({'error': 'unauthorized'}), 401

    from extensions import db
    from models import User

    # Create tables if they don't exist
    db.create_all()

    users_data = [
        {'username': 'president1', 'full_name': 'Jean Dupont', 'email': 'president@unissonslamain.local', 'phone': '+250789123456', 'role': 'president'},
        {'username': 'tresorier1', 'full_name': 'Marie Traore', 'email': 'tresorier@unissonslamain.local', 'phone': '+250789123457', 'role': 'tresorier'},
        {'username': 'secretaire1', 'full_name': 'Sophie Bernard', 'email': 'secretaire@unissonslamain.local', 'phone': '+250789123458', 'role': 'secretaire'},
        {'username': 'member1', 'full_name': 'Pierre Martin', 'email': 'member1@unissonslamain.local', 'phone': '+250789123459', 'role': 'member'},
        {'username': 'member2', 'full_name': 'Alice Johnson', 'email': 'member2@unissonslamain.local', 'phone': '+250789123460', 'role': 'member'},
        {'username': 'member3', 'full_name': 'Bob Leblanc', 'email': 'member3@unissonslamain.local', 'phone': '+250789123461', 'role': 'member'},
    ]

    created = 0
    updated = 0
    for u in users_data:
        user = db.session.query(User).filter_by(username=u['username']).first()
        if user:
            user.full_name = u['full_name']
            user.email = u['email']
            user.phone = u['phone']
            user.role = u['role']
            user.is_active = True
            user.set_password('password123')
            updated += 1
        else:
            user = User(**u, is_active=True)
            user.set_password('password123')
            db.session.add(user)
            created += 1

    db.session.commit()
    return jsonify({'status': 'seeded', 'created': created, 'updated': updated}), 200


@bp.route('/admin/users-count', methods=['GET'])
def users_count():
    """Count users by role (public endpoint for info)"""
    from extensions import db
    from models import User
    
    total = db.session.query(User).count()
    by_role = db.session.query(
        User.role,
        func.count(User.id)
    ).group_by(User.role).all()
    
    users_list = db.session.query(
        User.username,
        User.full_name,
        User.role,
        User.is_active,
        User.email,
        User.phone
    ).order_by(User.role, User.username).all()
    
    return jsonify({
        'total': total,
        'by_role': {role: count for role, count in by_role},
        'users': [
            {
                'username': u[0],
                'full_name': u[1],
                'role': u[2],
                'active': u[3],
                'email': u[4],
                'phone': u[5]
            }
            for u in users_list
        ]
    }), 200
