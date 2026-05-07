from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User
from datetime import datetime

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
