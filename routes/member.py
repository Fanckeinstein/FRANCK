from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import User, Contribution, Loan, Transaction
from datetime import datetime, timedelta
from sqlalchemy import func
from verification.utils import send_email

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
        amount_raw = data.get('amount')
        amount = float(amount_raw) if amount_raw not in (None, '') else None
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


@member_bp.route('/request-contribution', methods=['GET', 'POST'])
def request_contribution():
    """Request a monthly contribution to be validated by the treasurer"""
    current_month = datetime.utcnow().strftime('%Y-%m')

    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        amount_raw = data.get('amount')
        amount = float(amount_raw) if amount_raw not in (None, '') else None
        month = data.get('month', current_month)

        if not amount:
            amount = 1000.0

        if amount <= 0:
            msg = 'Le montant doit être positif'
            if request.is_json:
                return jsonify({'ok': False, 'error': msg}), 400
            flash(msg, 'danger')
            return redirect(url_for('member.request_contribution'))

        contribution = db.session.query(Contribution).filter_by(
            user_id=current_user.id,
            month=month
        ).first()

        if contribution and contribution.status == 'paid':
            msg = 'Cette cotisation est déjà validée'
            if request.is_json:
                return jsonify({'ok': False, 'error': msg}), 400
            flash(msg, 'warning')
            return redirect(url_for('member.dashboard'))

        if not contribution:
            contribution = Contribution(
                user_id=current_user.id,
                amount=amount,
                month=month,
                status='pending'
            )
            db.session.add(contribution)
        else:
            contribution.amount = amount
            contribution.status = 'pending'
            contribution.payment_method = None
            contribution.payment_proof = None
            contribution.paid_at = None
            contribution.validated_by = None

        db.session.commit()

        treasurers = db.session.query(User).filter(
            User.role == 'tresorier',
            User.is_active == True,
            User.email.isnot(None)
        ).all()

        email_subject = f'Nouvelle cotisation en attente - {month}'
        email_body = (
            f"Bonjour,\n\n"
            f"Une nouvelle cotisation attend votre validation.\n\n"
            f"Membre: {current_user.full_name} (@{current_user.username})\n"
            f"Mois: {month}\n"
            f"Montant: {amount:.0f} FCFA\n"
            f"Statut: en attente\n\n"
            f"Connectez-vous puis ouvrez la page cotisations pour valider: /tresorier/contributions?status=pending&month={month}\n\n"
            f"Cordialement,\nUnissons la Main"
        )

        for treasurer in treasurers:
            send_email(treasurer.email, email_subject, email_body)

        if request.is_json:
            return jsonify({'ok': True, 'message': 'Cotisation envoyée pour validation', 'contribution_id': contribution.id}), 201

        flash('Cotisation envoyée pour validation par la trésorière. Vous recevrez une confirmation après validation.', 'success')
        return redirect(url_for('member.dashboard'))

    return render_template('member/request_contribution.html', current_month=current_month)


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
