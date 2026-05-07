from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import User, Contribution, Loan, Transaction
from datetime import datetime
from sqlalchemy import func

president_bp = Blueprint('president', __name__, url_prefix='/president', template_folder='../templates')


@president_bp.before_request
@login_required
def check_role():
    """Ensure only presidents access this blueprint"""
    if current_user.role != 'president':
        return jsonify({'error': 'Unauthorized'}), 403


@president_bp.route('/dashboard')
def dashboard():
    """President dashboard"""
    # Get all statistics
    total_members = db.session.query(func.count(User.id)).filter_by(role='member').scalar()
    total_contributions = db.session.query(func.sum(Contribution.amount)).filter_by(status='paid').scalar() or 0
    total_loans_approved = db.session.query(func.sum(Loan.amount)).filter_by(status='approved').scalar() or 0
    total_loans_pending = db.session.query(func.count(Loan.id)).filter_by(status='pending').scalar()
    
    treasury_balance = float(total_contributions) - float(total_loans_approved)
    
    # Pending loan requests
    pending_loans = db.session.query(Loan).filter_by(status='pending').order_by(
        Loan.requested_at.desc()
    ).all()
    
    # Monthly contribution status
    current_month = datetime.utcnow().strftime('%Y-%m')
    contrib_status = db.session.query(
        Contribution.status,
        func.count(Contribution.id)
    ).filter_by(month=current_month).group_by(Contribution.status).all()
    
    return render_template('president/dashboard.html',
        total_members=total_members,
        total_contributions=float(total_contributions),
        total_loans_approved=float(total_loans_approved),
        total_loans_pending=total_loans_pending,
        treasury_balance=treasury_balance,
        pending_loans=pending_loans,
        contrib_status=dict(contrib_status),
        current_month=current_month
    )


@president_bp.route('/loans')
def loans():
    """View all loan requests"""
    status = request.args.get('status', 'all')
    
    query = Loan.query
    if status != 'all':
        query = query.filter_by(status=status)
    
    loans = query.order_by(Loan.requested_at.desc()).all()
    
    return render_template('president/loans.html', loans=loans, status=status)


@president_bp.route('/api/loan/<int:loan_id>/approve', methods=['POST'])
@login_required
def approve_loan(loan_id):
    """Approve a loan request"""
    if current_user.role != 'president':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    approval_notes = data.get('approval_notes', '')
    repayment_days = data.get('repayment_days', 30)
    
    loan = db.session.query(Loan).filter_by(id=loan_id).first()
    if not loan:
        return jsonify({'error': 'Loan not found'}), 404
    
    loan.status = 'approved'
    loan.approved_at = datetime.utcnow()
    loan.approved_by = current_user.id
    loan.approval_notes = approval_notes
    loan.repayment_deadline = datetime.utcnow() + __import__('datetime').timedelta(days=repayment_days)
    
    db.session.commit()
    
    # Create transaction log
    transaction = Transaction(
        type='loan_approved',
        user_id=loan.user_id,
        amount=loan.amount,
        description=f'Loan approved by {current_user.full_name}',
        reference_id=loan.id
    )
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify({'ok': True, 'message': 'Loan approved'})


@president_bp.route('/api/loan/<int:loan_id>/reject', methods=['POST'])
@login_required
def reject_loan(loan_id):
    """Reject a loan request"""
    if current_user.role != 'president':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    rejection_reason = data.get('reason', 'No reason provided')
    
    loan = db.session.query(Loan).filter_by(id=loan_id).first()
    if not loan:
        return jsonify({'error': 'Loan not found'}), 404
    
    loan.status = 'rejected'
    loan.approval_notes = rejection_reason
    db.session.commit()
    
    # Create transaction log
    transaction = Transaction(
        type='loan_rejected',
        user_id=loan.user_id,
        amount=loan.amount,
        description=f'Loan rejected: {rejection_reason}',
        reference_id=loan.id
    )
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify({'ok': True, 'message': 'Loan rejected'})


@president_bp.route('/members')
def members():
    """View all members"""
    members = db.session.query(User).filter_by(role='member').all()
    
    return render_template('president/members.html', members=members)


@president_bp.route('/reports')
def reports():
    """View reports and statistics"""
    # Year-to-date stats
    year = datetime.utcnow().year
    monthly_contributions = db.session.query(
        func.strftime('%Y-%m', Contribution.paid_at),
        func.sum(Contribution.amount)
    ).filter(
        Contribution.status == 'paid',
        db.func.strftime('%Y', Contribution.paid_at) == str(year)
    ).group_by(func.strftime('%Y-%m', Contribution.paid_at)).all()
    
    return render_template('president/reports.html', monthly_contributions=monthly_contributions)
