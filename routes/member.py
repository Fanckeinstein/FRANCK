from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import User, Contribution, Loan, Transaction
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from verification.utils import send_email, send_whatsapp
from werkzeug.utils import secure_filename
import os
import re
try:
    import pytesseract
    from PIL import Image
    OCR_ENABLED = True
except Exception:
    pytesseract = None
    Image = None
    OCR_ENABLED = False


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
        extract('year', Contribution.paid_at) == year
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


@member_bp.route('/admin-team')
def admin_team():
    """Show administrative team contacts to members."""
    admin_team = db.session.query(User).filter(
        User.role.in_(['president', 'tresorier', 'secretaire']),
        User.is_active == True
    ).order_by(User.role.asc(), User.full_name.asc()).all()

    role_labels = {
        'president': 'President',
        'tresorier': 'Tresorier',
        'secretaire': 'Secretaire'
    }

    return render_template('member/admin_team.html', admin_team=admin_team, role_labels=role_labels)


@member_bp.route('/request-loan', methods=['GET', 'POST'])
def request_loan():
    """Request an emergency loan"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        amount_raw = data.get('amount')
        amount = float(amount_raw) if amount_raw not in (None, '') else None
        reason = data.get('reason')
        loan_policy_acceptance = data.get('loan_policy_acceptance')
        
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

        if loan_policy_acceptance not in ['yes', 'on', True]:
            msg = 'Vous devez accepter la politique de remboursement avant de continuer.'
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

        # Handle uploaded proof and payment reference if provided
        if not request.is_json:
            # payment_reference and file upload
            payment_reference = request.form.get('payment_reference')
            file = request.files.get('payment_proof')
            if file:
                uploads_dir = os.path.join(os.getcwd(), 'static', 'uploads', 'receipts')
                os.makedirs(uploads_dir, exist_ok=True)
                filename = secure_filename(f"{current_user.username}_{month}_{file.filename}")
                filepath = os.path.join(uploads_dir, filename)
                file.save(filepath)
                contribution.payment_proof = os.path.relpath(filepath, os.getcwd()).replace('\\','/')
                # Try OCR extraction of payment reference from image (if available)
                if OCR_ENABLED and not contribution.payment_reference:
                    try:
                        img = Image.open(filepath)
                        text = pytesseract.image_to_string(img)
                        # Look for transaction ID patterns:
                        # Orange Money: MP260508.1340.3149810 or MP26050813403149810
                        # MTN: TX-prefix or TXID patterns
                        # Generic: REF + numbers or ID + numbers
                        patterns = [
                            r"\b(MP[0-9\.]+([\s\.])?[0-9\.]+)\b",  # Orange Money
                            r"\b(TX[0-9\.]+)\b",  # MTN/Generic TX
                            r"\b(REF[:\s-]*[0-9\.]+)\b",  # REF: prefix
                            r"\b(ID[:\s-]*[0-9]+)\b",  # ID: prefix
                        ]
                        for pattern in patterns:
                            m = re.search(pattern, text, re.IGNORECASE)
                            if m:
                                found = m.group(1).strip().replace(' ', '')
                                if len(found) > 5:  # Avoid noise; trans IDs are typically > 5 chars
                                    contribution.payment_reference = found
                                    break
                    except Exception:
                        pass
            if payment_reference:
                contribution.payment_reference = payment_reference

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
            if treasurer.phone:
                send_whatsapp(treasurer.phone, email_body)

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

    _send_contribution_confirmation(contribution)
    
    return jsonify({'ok': True, 'message': 'Contribution marked as paid'})
