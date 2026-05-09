from flask import Blueprint, request, jsonify, current_app
import os

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

    # Check existing
    if db.session.query(User).first():
        return jsonify({'status': 'already_seeded'}), 200

    users_data = [
        {'username': 'president1', 'full_name': 'Jean Dupont', 'email': 'president@unissonslamain.local', 'phone': '+250789123456', 'role': 'president'},
        {'username': 'tresorier1', 'full_name': 'Marie Traore', 'email': 'tresorier@unissonslamain.local', 'phone': '+250789123457', 'role': 'tresorier'},
        {'username': 'secretaire1', 'full_name': 'Sophie Bernard', 'email': 'secretaire@unissonslamain.local', 'phone': '+250789123458', 'role': 'secretaire'},
        {'username': 'member1', 'full_name': 'Pierre Martin', 'email': 'member1@unissonslamain.local', 'phone': '+250789123459', 'role': 'member'},
        {'username': 'member2', 'full_name': 'Alice Johnson', 'email': 'member2@unissonslamain.local', 'phone': '+250789123460', 'role': 'member'},
        {'username': 'member3', 'full_name': 'Bob Leblanc', 'email': 'member3@unissonslamain.local', 'phone': '+250789123461', 'role': 'member'},
    ]

    users = []
    for u in users_data:
        user = User(**u, is_active=True)
        user.set_password('password123')
        db.session.add(user)
        users.append(user)

    db.session.commit()
    return jsonify({'status': 'seeded', 'count': len(users)}), 201
