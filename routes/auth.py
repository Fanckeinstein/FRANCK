from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User, VerificationCode
from datetime import datetime, timedelta
from verification.utils import generate_code, send_email, send_whatsapp

auth_bp = Blueprint('auth', __name__, template_folder='../templates')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login endpoint"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            if request.is_json:
                return jsonify({'ok': False, 'error': 'Username and password required'}), 400
            flash('Username and password required', 'danger')
            return redirect(url_for('auth.login'))

        user = db.session.query(User).filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            if request.is_json:
                return jsonify({'ok': False, 'error': 'Invalid credentials'}), 401
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))

        if not user.is_active:
            if request.is_json:
                return jsonify({'ok': False, 'error': 'Account not verified'}), 403
            flash('Account not verified. Please check your email.', 'warning')
            return redirect(url_for('auth.login'))

        login_user(user, remember=data.get('remember', False))
        
        if request.is_json:
            return jsonify({'ok': True, 'message': 'Logged in', 'role': user.role})
        
        # Redirect based on role
        role_redirects = {
            'president': 'president.dashboard',
            'tresorier': 'tresorier.dashboard',
            'secretaire': 'secretaire.dashboard',
            'member': 'member.dashboard'
        }
        return redirect(url_for(role_redirects.get(user.role, 'index')))

    return render_template('auth/login.html')


@auth_bp.route('/logout', methods=['POST', 'GET'])
@login_required
def logout():
    """User logout endpoint"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration endpoint"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        full_name = data.get('full_name')
        email = data.get('email')
        phone = data.get('phone')
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        # Validation
        if not username or not full_name or not password:
            msg = 'Username, full name and password are required'
            if request.is_json:
                return jsonify({'ok': False, 'error': msg}), 400
            flash(msg, 'danger')
            return redirect(url_for('auth.register'))

        if password != confirm_password:
            msg = 'Passwords do not match'
            if request.is_json:
                return jsonify({'ok': False, 'error': msg}), 400
            flash(msg, 'danger')
            return redirect(url_for('auth.register'))

        if len(password) < 6:
            msg = 'Password must be at least 6 characters'
            if request.is_json:
                return jsonify({'ok': False, 'error': msg}), 400
            flash(msg, 'danger')
            return redirect(url_for('auth.register'))

        # Check if user exists
        if db.session.query(User).filter_by(username=username).first():
            msg = 'Username already exists'
            if request.is_json:
                return jsonify({'ok': False, 'error': msg}), 400
            flash(msg, 'danger')
            return redirect(url_for('auth.register'))

        if email and db.session.query(User).filter_by(email=email).first():
            msg = 'Email already registered'
            if request.is_json:
                return jsonify({'ok': False, 'error': msg}), 400
            flash(msg, 'danger')
            return redirect(url_for('auth.register'))

        # Create user
        user = User(
            username=username,
            full_name=full_name,
            email=email,
            phone=phone,
            role='member',
            is_active=True  # Auto-activate for now (in prod, require email verification)
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        if request.is_json:
            return jsonify({'ok': True, 'message': 'User created successfully'}), 201
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Start password reset by sending a verification code."""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        identifier = (data.get('identifier') or '').strip()

        if not identifier:
            msg = 'Veuillez renseigner votre nom utilisateur, email ou numero.'
            if request.is_json:
                return jsonify({'ok': False, 'error': msg}), 400
            flash(msg, 'danger')
            return redirect(url_for('auth.forgot_password'))

        user = db.session.query(User).filter(
            (User.username == identifier) |
            (User.email == identifier) |
            (User.phone == identifier)
        ).first()

        # Return a generic message even when no account is found.
        success_msg = 'Si ce compte existe, un code de reinitialisation a ete envoye.'

        if user:
            code = generate_code()
            expires = datetime.utcnow() + timedelta(minutes=15)

            vc = VerificationCode(
                user_id=user.id,
                email=user.email,
                phone=user.phone,
                code=code,
                purpose='reset_password',
                expires_at=expires,
                verified=False
            )
            db.session.add(vc)
            db.session.commit()

            subject = 'Code de reinitialisation du mot de passe'
            body = (
                f"Bonjour {user.full_name},\n\n"
                f"Voici votre code de reinitialisation: {code}\n"
                f"Ce code expire dans 15 minutes.\n\n"
                f"Si vous n'etes pas a l'origine de cette demande, ignorez ce message.\n\n"
                f"Unissons la Main"
            )

            if user.email:
                send_email(user.email, subject, body)
            if user.phone:
                send_whatsapp(user.phone, body)

        if request.is_json:
            return jsonify({'ok': True, 'message': success_msg})

        flash(success_msg, 'success')
        return redirect(url_for('auth.reset_password'))

    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Reset password with optional verification code (fallback mode without reception check)."""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = (data.get('username') or '').strip()
        code = (data.get('code') or '').strip()
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        if not username or not new_password or not confirm_password:
            msg = 'Tous les champs sont obligatoires.'
            if request.is_json:
                return jsonify({'ok': False, 'error': msg}), 400
            flash(msg, 'danger')
            return redirect(url_for('auth.reset_password'))

        if new_password != confirm_password:
            msg = 'Les mots de passe ne correspondent pas.'
            if request.is_json:
                return jsonify({'ok': False, 'error': msg}), 400
            flash(msg, 'danger')
            return redirect(url_for('auth.reset_password'))

        if len(new_password) < 6:
            msg = 'Le mot de passe doit contenir au moins 6 caracteres.'
            if request.is_json:
                return jsonify({'ok': False, 'error': msg}), 400
            flash(msg, 'danger')
            return redirect(url_for('auth.reset_password'))

        user = db.session.query(User).filter_by(username=username).first()
        if not user:
            msg = 'Compte introuvable.'
            if request.is_json:
                return jsonify({'ok': False, 'error': msg}), 400
            flash(msg, 'danger')
            return redirect(url_for('auth.reset_password'))

        verification = None
        if code:
            verification = db.session.query(VerificationCode).filter(
                VerificationCode.user_id == user.id,
                VerificationCode.purpose == 'reset_password',
                VerificationCode.code == code,
                VerificationCode.verified == False,
                VerificationCode.expires_at >= datetime.utcnow()
            ).order_by(VerificationCode.created_at.desc()).first()

            if not verification:
                msg = 'Code invalide ou expire.'
                if request.is_json:
                    return jsonify({'ok': False, 'error': msg}), 400
                flash(msg, 'danger')
                return redirect(url_for('auth.reset_password'))

        user.set_password(new_password)
        user.updated_at = datetime.utcnow()

        if verification:
            verification.verified = True

        db.session.commit()

        success_msg = 'Mot de passe reinitialise avec succes. Vous pouvez vous connecter.'
        if request.is_json:
            return jsonify({'ok': True, 'message': success_msg})

        flash(success_msg, 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html')


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        current_user.full_name = data.get('full_name', current_user.full_name)
        current_user.email = data.get('email', current_user.email)
        current_user.phone = data.get('phone', current_user.phone)
        current_user.updated_at = datetime.utcnow()
        
        # Change password if provided
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if old_password and new_password:
            if not current_user.check_password(old_password):
                msg = 'Current password is incorrect'
                if request.is_json:
                    return jsonify({'ok': False, 'error': msg}), 400
                flash(msg, 'danger')
                return redirect(url_for('auth.profile'))
            
            current_user.set_password(new_password)
        
        db.session.commit()
        
        if request.is_json:
            return jsonify({'ok': True, 'message': 'Profile updated'})
        
        flash('Profile updated successfully', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html', user=current_user)
