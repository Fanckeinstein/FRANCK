from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, send_file
from urllib.parse import quote_plus
from flask_login import login_required, current_user
from extensions import db
from models import User, Contribution, Loan, Transaction
from datetime import datetime, timedelta
from sqlalchemy import func
from verification.utils import send_email, send_whatsapp
import io

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
    payment_reference = data.get('payment_reference')

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
    if payment_reference:
        contribution.payment_reference = payment_reference
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
    # Build WhatsApp links to open on treasurer device (mobile deep link + web link)
    member = db.session.get(User, contribution.user_id)
    whatsapp_links = None
    if member and member.phone:
        # Normalize phone to digits only (keep '+' if present)
        digits = ''.join([c for c in (member.phone or '') if c.isdigit() or c == '+'])
        if digits.startswith('00'):
            digits = digits[2:]
        text = (
            f"Bonjour {member.full_name}, votre cotisation pour {contribution.month} de "
            f"{int(contribution.amount)} FCFA a ete validee par {current_user.full_name}."
        )
        if contribution.payment_reference:
            text += f" Reference: {contribution.payment_reference}."
        q = quote_plus(text)
        whatsapp_links = {
            'web': f'https://wa.me/{digits}?text={q}',
            'mobile': f'whatsapp://send?phone={digits}&text={q}'
        }

    # If request came from JS/API return JSON including WhatsApp links so treasurer can open it
    if request.is_json or request.headers.get('Accept', '').startswith('application/json'):
        resp = {'ok': True, 'message': 'Contribution validated'}
        if whatsapp_links:
            resp['whatsapp'] = whatsapp_links
        return jsonify(resp)

    # For form-based flow, redirect to wa.me (opens WhatsApp web or app)
    if whatsapp_links:
        return redirect(whatsapp_links['web'])

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


def _month_expr(col):
    """Return a SQL expression that extracts YYYY-MM from a datetime column in a DB-agnostic way."""
    # Use engine dialect name (more reliable) and map to the appropriate function
    try:
        dialect_name = (db.engine.dialect.name or '').lower()
    except Exception:
        dialect_name = 'sqlite'

    if 'sqlite' in dialect_name:
        return func.strftime('%Y-%m', col)
    # Postgres
    if 'postgres' in dialect_name or 'postgresql' in dialect_name:
        return func.to_char(col, 'YYYY-MM')
    # Fallback to to_char if available
    return func.to_char(col, 'YYYY-MM')


@tresorier_bp.route('/api/report/<month>')
@login_required
def api_report(month):
    """Return a treasurer report for a given month as JSON."""
    if current_user.role not in ['tresorier', 'president']:
        return jsonify({'error': 'Unauthorized'}), 403

    # Contributions summary by status for the month
    contrib_rows = db.session.query(
        func.coalesce(func.count(Contribution.id), 0),
        func.coalesce(func.sum(Contribution.amount), 0),
        Contribution.status
    ).filter(Contribution.month == month).group_by(Contribution.status).all()

    # Per-member totals (paid only)
    per_member = db.session.query(
        User.id,
        User.full_name,
        func.coalesce(func.sum(Contribution.amount), 0)
    ).join(Contribution, Contribution.user_id == User.id).filter(
        Contribution.month == month,
        Contribution.status == 'paid'
    ).group_by(User.id, User.full_name).order_by(User.full_name).all()

    # Transactions for the month
    month_expr = _month_expr(Transaction.created_at)
    transactions = db.session.query(Transaction).filter(month_expr == month).order_by(Transaction.created_at.desc()).limit(1000).all()

    # Loans summary (approved/repaid) for context
    loan_month_expr = _month_expr(Loan.requested_at)
    loans_approved = db.session.query(func.count(Loan.id), func.coalesce(func.sum(Loan.amount), 0)).filter(
        loan_month_expr == month,
        Loan.status == 'approved'
    ).first()

    return jsonify({
        'month': month,
        'contributions': [
            {'status': r[2], 'count': int(r[0] or 0), 'amount': float(r[1] or 0)} for r in contrib_rows
        ],
        'per_member': [
            {'user_id': m[0], 'full_name': m[1], 'amount': float(m[2] or 0)} for m in per_member
        ],
        'transactions': [
            {
                'id': t.id,
                'type': t.type,
                'user_id': t.user_id,
                'amount': float(t.amount),
                'description': t.description,
                'created_at': t.created_at.isoformat()
            } for t in transactions
        ],
        'loans_approved_count': int(loans_approved[0] or 0) if loans_approved else 0,
        'loans_approved_amount': float(loans_approved[1] or 0) if loans_approved else 0
    })


@tresorier_bp.route('/report/export/<format>')
@login_required
def export_report(format):
    """Export treasurer report for a month as CSV (format=csv)."""
    if current_user.role not in ['tresorier', 'president']:
        return jsonify({'error': 'Unauthorized'}), 403

    month = request.args.get('month', datetime.utcnow().strftime('%Y-%m'))

    if format != 'csv':
        return jsonify({'error': 'Format not supported'}), 400

    # Build CSV: transactions + contributions
    output = io.StringIO()
    writer = __import__('csv').writer(output)

    writer.writerow(['Section'])
    writer.writerow(['Contributions for', month])
    writer.writerow(['Status', 'Count', 'Amount'])
    contrib_rows = db.session.query(
        func.coalesce(func.count(Contribution.id), 0),
        func.coalesce(func.sum(Contribution.amount), 0),
        Contribution.status
    ).filter(Contribution.month == month).group_by(Contribution.status).all()
    for r in contrib_rows:
        writer.writerow([r[2], int(r[0] or 0), float(r[1] or 0)])

    writer.writerow([])
    writer.writerow(['Per member (paid)'])
    writer.writerow(['Member', 'Amount'])
    per_member = db.session.query(
        User.full_name,
        func.coalesce(func.sum(Contribution.amount), 0)
    ).join(Contribution, Contribution.user_id == User.id).filter(
        Contribution.month == month,
        Contribution.status == 'paid'
    ).group_by(User.full_name).order_by(User.full_name).all()
    for m in per_member:
        writer.writerow([m[0], float(m[1] or 0)])

    writer.writerow([])
    writer.writerow(['Transactions'])
    writer.writerow(['Type', 'User', 'Amount', 'Date', 'Description'])
    month_expr = _month_expr(Transaction.created_at)
    transactions = db.session.query(Transaction).filter(month_expr == month).order_by(Transaction.created_at.desc()).all()
    for t in transactions:
        user = db.session.get(User, t.user_id)
        writer.writerow([t.type, user.full_name if user else '', float(t.amount), t.created_at.isoformat(), t.description])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'tresorier_report_{month}.csv'
    )
