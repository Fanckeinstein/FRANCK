from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from extensions import db
from models import User, Contribution, Loan, Transaction
from sqlalchemy import func
from datetime import datetime, timedelta

common_bp = Blueprint('common', __name__, template_folder='../templates')


@common_bp.route('/')
@common_bp.route('/index')
def index():
    """Home page - redirects based on auth status"""
    if current_user.is_authenticated:
        role_redirects = {
            'president': 'president.dashboard',
            'tresorier': 'tresorier.dashboard',
            'secretaire': 'secretaire.dashboard',
            'member': 'member.dashboard'
        }
        from flask import redirect, url_for
        return redirect(url_for(role_redirects.get(current_user.role, 'common.index')))
    
    return render_template('index.html')


@common_bp.route('/dashboard')
@login_required
def dashboard():
    """Generic dashboard - role-specific redirects handled by role blueprints"""
    role_redirects = {
        'president': 'president.dashboard',
        'tresorier': 'tresorier.dashboard',
        'secretaire': 'secretaire.dashboard',
        'member': 'member.dashboard'
    }
    from flask import redirect, url_for
    return redirect(url_for(role_redirects.get(current_user.role, 'common.index')))


@common_bp.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    """Get general statistics (role-dependent)"""
    total_members = db.session.query(func.count(User.id)).filter_by(role='member', is_active=True).scalar()
    total_contributions = db.session.query(func.sum(Contribution.amount)).filter_by(status='paid').scalar() or 0
    total_loans = db.session.query(func.sum(Loan.amount)).filter_by(status='approved').scalar() or 0
    
    stats = {
        'total_members': total_members,
        'total_contributions': float(total_contributions),
        'total_loans': float(total_loans),
        'treasury_balance': float(total_contributions) - float(total_loans)
    }
    
    return jsonify(stats)


@common_bp.route('/api/transactions', methods=['GET'])
@login_required
def get_transactions():
    """Get transaction history (role-dependent filtering)"""
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    query = Transaction.query.order_by(Transaction.created_at.desc())
    
    # Members only see their own transactions
    if current_user.role == 'member':
        query = query.filter_by(user_id=current_user.id)
    
    total = query.count()
    transactions = query.limit(limit).offset(offset).all()
    
    return jsonify({
        'total': total,
        'limit': limit,
        'offset': offset,
        'transactions': [{
            'id': t.id,
            'type': t.type,
            'user': User.query.get(t.user_id).full_name,
            'amount': float(t.amount),
            'description': t.description,
            'date': t.created_at.isoformat()
        } for t in transactions]
    })
