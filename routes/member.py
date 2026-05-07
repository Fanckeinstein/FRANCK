from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import User, Contribution, Loan, Transaction
from datetime import datetime, timedelta
from sqlalchemy import func

member_bp = Blueprint('member', __name__, url_prefix='/member', template_folder='../templates')


@member_bp.before_request
@login_required
def check_role():
    """Ensure only members access this blueprint"""
    if current_user.role not in ['member', 'president', 'tresorier', 'secretaire']:
        return jsonify({'error': 'Unauthorized'}), 403


@member_bp.route('/dashboard')
def dashboard():
    """Member dashboard"""
    # Current month contributions status
    current_month = datetime.utcnow().strftime('%Y-%m')
    contribution = db.session.query(Contribution).filter_by(
        user_id=current_user.id,
        month=current_month
    ).first()
    
    # Recent loans
    recent_loans = db.session.query(Loan).filter_by(user_id=current_user.id).order_by(
        Loan.requested_at.desc()
    ).limit(5).all()
    
    # Recent contributions
    recent_contributions = db.session.query(Contribution).filter_by(
        user_id=current_user.id
    ).order_by(Contribution.created_at.desc()).limit(10).all()
    
    # Total paid this year
    year = datetime.utcnow().year
    total_paid_year = db.session.query(func.sum(Contribution.amount)).filter(
        Contribution.user_id == current_user.id,
        Contribution.status == 'paid',
        db.func.strftime('%Y', Contribution.paid_at) == str(year)
    ).scalar() or 0
    
    # Treasury balance
    total_contributions = db.session.query(func.sum(Contribution.amount)).filter_by(
        status='paid'
    ).scalar() or 0
    total_loans = db.session.query(func.sum(Loan.amount)).filter_by(
        status='approved'
    ).scalar() or 0
    treasury_balance = float(total_contributions) - float(total_loans)
    
    return render_template('member/dashboard.html',
        contribution=contribution,
        recent_loans=recent_loans,
        recent_contributions=recent_contributions,
        total_paid_year=float(total_paid_year),
        treasury_balance=treasury_balance,
        current_month=current_month
    )


@member_bp.route('/contributions')
def contributions():
    """View contribution history"""
    contributions = db.session.query(Contribution).filter_by(
        user_id=current_user.id
    ).order_by(Contribution.created_at.desc()).all()
    
    return render_template('member/contributions.html', contributions=contributions)


@member_bp.route('/loans')
def loans():
    """View loans"""
    loans = db.session.query(Loan).filter_by(user_id=current_user.id).order_by(
        Loan.requested_at.desc()
    ).all()
    
    return render_template('member/loans.html', loans=loans)


@member_bp.route('/request-loan', methods=['GET', 'POST'])
def request_loan():
    """Request an emergency loan"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        amount = data.get('amount', type=float)
        reason = data.get('reason')
        
        if not amount or not reason:
            msg = 'Amount and reason are required'
            if request.is_json:
                return jsonify({'ok': False, 'error': msg}), 400
            flash(msg, 'danger')
            return redirect(url_for('member.request_loan'))
        
        if amount <= 0:
            msg = 'Amount must be positive'
            if request.is_json:
                return jsonify({'ok': False, 'error': msg}), 400
            flash(msg, 'danger')
            return redirect(url_for('member.request_loan'))
        
        # Create loan request
        loan = Loan(
            user_id=current_user.id,
            amount=amount,
            reason=reason,
            status='pending'
        )
        db.session.add(loan)
        db.session.commit()
        
        # Create transaction log
        transaction = Transaction(
            type='loan_requested',
            user_id=current_user.id,
            amount=amount,
            description=f'Loan request: {reason}',
            reference_id=loan.id
        )
        db.session.add(transaction)
        db.session.commit()
        
        if request.is_json:
            return jsonify({'ok': True, 'message': 'Loan request submitted', 'loan_id': loan.id}), 201
        
        flash('Loan request submitted. Awaiting approval from president.', 'success')
        return redirect(url_for('member.loans'))
    
    return render_template('member/request_loan.html')


@member_bp.route('/api/pay-contribution', methods=['POST'])
@login_required
def pay_contribution():
    """Mark contribution as paid (for treasurer)"""
    if current_user.role not in ['tresorier', 'president']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    contribution_id = data.get('contribution_id')
    payment_method = data.get('payment_method')
    
    contribution = db.session.query(Contribution).filter_by(id=contribution_id).first()
    if not contribution:
        return jsonify({'error': 'Contribution not found'}), 404
    
    contribution.status = 'paid'
    contribution.payment_method = payment_method
    contribution.paid_at = datetime.utcnow()
    contribution.validated_by = current_user.id
    db.session.commit()
    
    # Create transaction log
    transaction = Transaction(
        type='contribution_paid',
        user_id=contribution.user_id,
        amount=contribution.amount,
        description=f'Contribution {contribution.month} - {payment_method}',
        reference_id=contribution.id
    )
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify({'ok': True, 'message': 'Contribution marked as paid'})
