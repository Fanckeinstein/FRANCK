from flask import request, jsonify
from . import bp
from extensions import db
from models import User, VerificationCode
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from .utils import generate_code, send_email, send_whatsapp


@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username')
    full_name = data.get('full_name')
    phone = data.get('phone')
    email = data.get('email')
    password = data.get('password')

    if not username or not full_name or not password:
        return jsonify({'ok': False, 'error': 'username, full_name and password required'}), 400

    # check existing
    if db.session.query(User).filter_by(username=username).first():
        return jsonify({'ok': False, 'error': 'username already exists'}), 400

    password_hash = generate_password_hash(password)
    user = User(username=username, password_hash=password_hash, full_name=full_name, role='member', is_active=False)
    db.session.add(user)
    db.session.commit()

    # generate code
    code = generate_code(6)
    expires = datetime.utcnow() + timedelta(minutes=15)
    vc = VerificationCode(user_id=user.id, email=email, phone=phone, code=code, purpose='register', expires_at=expires)
    db.session.add(vc)
    db.session.commit()

    subject = 'Votre code de vérification Unissons la Main'
    body = f"Votre code de vérification est: {code} (valable 15 minutes)"

    if email:
        send_email(email, subject, body)
    if phone:
        send_whatsapp(phone, body)

    return jsonify({'ok': True, 'message': 'user created, code sent'})


@bp.route('/verify', methods=['POST'])
def verify():
    data = request.get_json() or {}
    username = data.get('username')
    code = data.get('code')

    if not username or not code:
        return jsonify({'ok': False, 'error': 'username and code required'}), 400

    user = db.session.query(User).filter_by(username=username).first()
    if not user:
        return jsonify({'ok': False, 'error': 'user not found'}), 404

    # find latest code
    vc = (db.session.query(VerificationCode)
          .filter_by(user_id=user.id, purpose='register', verified=False)
          .order_by(VerificationCode.created_at.desc())
          .first())

    if not vc:
        return jsonify({'ok': False, 'error': 'no verification code found'}), 404

    if vc.expires_at and vc.expires_at < datetime.utcnow():
        return jsonify({'ok': False, 'error': 'code expired'}), 400

    if vc.code != code:
        return jsonify({'ok': False, 'error': 'invalid code'}), 400

    vc.verified = True
    user.is_active = True
    db.session.commit()

    return jsonify({'ok': True, 'message': 'verified'})
