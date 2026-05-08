from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import User, Contribution, Loan, Transaction
from datetime import datetime, timedelta
from sqlalchemy import func
from verification.utils import send_email, send_whatsapp

tresorier_bp = Blueprint('tresorier', __name__, url_prefix='/tresorier', template_folder='../templates')


def _send_contribution_confirmation(contribution):
    """Send the default confirmation message to the member after payment validation."""
    member = db.session.get(User, contribution.user_id)
    if not member:
        return

    subject = f'Confirmation de votre cotisation - {contribution.month}'
    body = (
        f"Bonjour {member.full_name},\n\n"
        f"Votre cotisation pour ce mois a bien été prise en compte.\n\n"
        f"Détails :\n"
        f"- Mois : {contribution.month}\n"
        f"- Montant : {float(contribution.amount):.0f} FCFA\n"
        f"- Moyen de paiement : {contribution.payment_method or 'non précisé'}\n\n"
        f"Merci pour votre contribution.\n"
        f"Unissons la Main"
    )
    if member.email:
        send_email(member.email, subject, body)
    if member.phone:
        send_whatsapp(member.phone, body)


@tresorier_bp.before_request
@login_required
def check_role():
    """Ensure only treasurers access this blueprint"""
    if current_user.role not in ['tresorier', 'president']:
        return jsonify({'error': 'Unauthorized'}), 403


@tresorier_bp.route('/dashboard')
def dashboard():
    """Treasurer dashboard"""
    # Treasury stats
    total_contributions = db.session.query(func.sum(Contribution.amount)).filter_by(status='paid').scalar() or 0
    total_loans = db.session.query(func.sum(Loan.amount)).filter_by(status='approved').scalar() or 0
    treasury_balance = float(total_contributions) - float(total_loans)
    
    # Current month contributions
    current_month = datetime.utcnow().strftime('%Y-%m')
    month_total = db.session.query(func.sum(Contribution.amount)).filter(
        Contribution.month == current_month,
        Contribution.status == 'paid'
    ).scalar() or 0
    
    # Pending contributions
    pending_count = db.session.query(func.count(Contribution.id)).filter(
        Contribution.month == current_month,
        Contribution.status == 'pending'
    ).scalar()
    
    # Recent transactions
    recent_transactions = db.session.query(Transaction).order_by(
        Transaction.created_at.desc()
    ).limit(10).all()
    
    return render_template('tresorier/dashboard.html',
        treasury_balance=treasury_balance,
        total_contributions=float(total_contributions),
        total_loans=float(total_loans),
        month_total=float(month_total),
        pending_count=pending_count,
        recent_transactions=recent_transactions,
        current_month=current_month
    )


@tresorier_bp.route('/contributions')
def contributions():
    """Manage contributions"""
    status = request.args.get('status', 'all')
    month = request.args.get('month', datetime.utcnow().strftime('%Y-%m'))
    
    query = Contribution.query.filter_by(month=month)
    if status != 'all':
        query = query.filter_by(status=status)
    
    contributions = query.order_by(Contribution.created_at.desc()).all()
    
    return render_template('tresorier/contributions.html',
        contributions=contributions,
        status=status,
        month=month
    )


@tresorier_bp.route('/api/contribution/validate', methods=['POST'])
@login_required
def validate_contribution():
    """Validate a contribution payment"""
    if current_user.role not in ['tresorier', 'president']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json(silent=True) or request.form
    if not data:
        return jsonify({'error': 'Invalid payload'}), 400

    contribution_id = data.get('contribution_id')
    payment_method = data.get('payment_method', 'cash')
    payment_proof = data.get('payment_proof')

    if not contribution_id:
        return jsonify({'error': 'Contribution ID is required'}), 400

    valid_methods = {'cash', 'mobile_money', 'bank'}
    if payment_method not in valid_methods:
        return jsonify({'error': 'Invalid payment method'}), 400
    
    contribution = db.session.query(Contribution).filter_by(id=contribution_id).first()
    if not contribution:
        return jsonify({'error': 'Contribution not found'}), 404

    if contribution.status == 'paid':
        return jsonify({'ok': True, 'message': 'Contribution already validated'})
    
    contribution.status = 'paid'
    contribution.payment_method = payment_method
    contribution.payment_proof = payment_proof
    contribution.paid_at = datetime.utcnow()
    contribution.validated_by = current_user.id
    
    db.session.commit()
    
    # Create transaction
    transaction = Transaction(
        type='contribution_validated',
        user_id=contribution.user_id,
        amount=contribution.amount,
        description=f'Contribution {contribution.month} validated ({payment_method})',
        reference_id=contribution.id
    )
    db.session.add(transaction)
    db.session.commit()

    _send_contribution_confirmation(contribution)
    
    return jsonify({'ok': True, 'message': 'Contribution validated'})


@tresorier_bp.route('/api/member/<int:member_id>/monthly-contribution', methods=['GET', 'POST'])
@login_required
def member_monthly_contribution(member_id):
    """Get or create monthly contribution for a member"""
    if current_user.role not in ['tresorier', 'president']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    member = db.session.query(User).filter_by(id=member_id, role='member').first()
    if not member:
        return jsonify({'error': 'Member not found'}), 404
    
    if request.method == 'GET':
        month = request.args.get('month', datetime.utcnow().strftime('%Y-%m'))
        contribution = db.session.query(Contribution).filter_by(
            user_id=member_id,
            month=month
        ).first()
        
        if contribution:
            return jsonify({
                'id': contribution.id,
                'user_id': contribution.user_id,
                'amount': float(contribution.amount),
                'month': contribution.month,
                'status': contribution.status,
                'payment_method': contribution.payment_method,
                'paid_at': contribution.paid_at.isoformat() if contribution.paid_at else None
            })
        return jsonify({'error': 'No contribution found'}), 404
    
    # POST - Create contribution if missing
    month = datetime.utcnow().strftime('%Y-%m')
    contribution = db.session.query(Contribution).filter_by(
        user_id=member_id,
        month=month
    ).first()
    
    if not contribution:
        contribution = Contribution(
            user_id=member_id,
            amount=1000.0,
            month=month,
            status='pending'
        )
        db.session.add(contribution)
        db.session.commit()
    
    return jsonify({
        'id': contribution.id,
        'user_id': contribution.user_id,
        'amount': float(contribution.amount),
        'month': contribution.month,
        'status': contribution.status
    }), 201


@tresorier_bp.route('/repayments')
def repayments():
    """View loan repayments"""
    loans = db.session.query(Loan).filter(
        Loan.status.in_(['approved', 'repaid'])
    ).order_by(Loan.repayment_deadline).all()
    
    return render_template('tresorier/repayments.html', loans=loans)


@tresorier_bp.route('/api/loan/<int:loan_id>/record-repayment', methods=['POST'])
@login_required
def record_repayment(loan_id):
    """Record a loan repayment"""
    if current_user.role not in ['tresorier', 'president']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    amount_raw = data.get('amount')
    amount = float(amount_raw) if amount_raw not in (None, '') else None
    if amount is None:
        return jsonify({'error': 'Amount is required'}), 400
    
    loan = db.session.query(Loan).filter_by(id=loan_id).first()
    if not loan:
        return jsonify({'error': 'Loan not found'}), 404
    
    loan.amount_repaid += amount
    if loan.amount_repaid >= loan.amount:
        loan.status = 'repaid'
        loan.repaid_at = datetime.utcnow()
    
    db.session.commit()
    
    # Create transaction
    transaction = Transaction(
        type='loan_repayment',
        user_id=loan.user_id,
        amount=amount,
        description=f'Loan repayment recorded',
        reference_id=loan.id
    )
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify({'ok': True, 'message': 'Repayment recorded'})
