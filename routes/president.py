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
    total_members = db.session.query(func.count(User.id)).filter_by(role='member', is_active=True).scalar()
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
    members = db.session.query(User).filter_by(role='member', is_active=True).all()
    
    return render_template('president/members.html', members=members)


@president_bp.route('/members/removed')
def removed_members():
    """View removed members"""
    members = db.session.query(User).filter_by(role='member', is_active=False).order_by(User.created_at.desc()).all()

    return render_template('president/removed_members.html', members=members)


@president_bp.route('/api/member/<int:member_id>/remove', methods=['POST'])
@login_required
def remove_member(member_id):
    """Deactivate a member account so the president can remove inactive members without deleting history."""
    if current_user.role != 'president':
        return jsonify({'error': 'Unauthorized'}), 403

    member = db.session.query(User).filter_by(id=member_id, role='member').first()
    if not member:
        return jsonify({'error': 'Member not found'}), 404

    if not member.is_active:
        return jsonify({'error': 'Member already removed'}), 400

    member.is_active = False

    from models import AuditLog

    audit = AuditLog(
        action='member_removed',
        performed_by=current_user.id,
        description=f'Membre retiré par le président: {member.full_name} (@{member.username})',
        affected_records=1,
        details=f'user_id={member.id}, role={member.role}, email={member.email or ""}, phone={member.phone or ""}',
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    db.session.commit()

    return jsonify({'ok': True, 'message': 'Member removed'})


@president_bp.route('/api/member/<int:member_id>/reactivate', methods=['POST'])
@login_required
def reactivate_member(member_id):
    """Reactivate a previously removed member."""
    if current_user.role != 'president':
        return jsonify({'error': 'Unauthorized'}), 403

    member = db.session.query(User).filter_by(id=member_id, role='member').first()
    if not member:
        return jsonify({'error': 'Member not found'}), 404

    if member.is_active:
        return jsonify({'error': 'Member already active'}), 400

    member.is_active = True

    from models import AuditLog

    audit = AuditLog(
        action='member_reactivated',
        performed_by=current_user.id,
        description=f'Membre réactivé par le président: {member.full_name} (@{member.username})',
        affected_records=1,
        details=f'user_id={member.id}, role={member.role}, email={member.email or ""}, phone={member.phone or ""}',
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    db.session.commit()

    return jsonify({'ok': True, 'message': 'Member reactivated'})


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
    
@president_bp.route('/audit-logs')
def audit_logs():
    """View all audit logs (immutable history)"""
    from models import AuditLog
    
    page = request.args.get('page', 1, type=int)
    logs = db.session.query(AuditLog).order_by(AuditLog.created_at.desc()).paginate(page=page, per_page=20)
    
    return render_template('president/audit_logs.html', logs=logs)
    
@president_bp.route('/admin/clear-data', methods=['GET', 'POST'])
def clear_data_page():
    """Clear transactional data (president only) - keep audit logs and users"""
    from models import AuditLog, Contribution, Loan, Transaction, MonthlySummary
    
    if request.method == 'POST':
        confirmation = request.form.get('confirmation', '')
        
        if confirmation.upper() != 'OUI':
            flash('Opération annulée - confirmation incorrecte', 'error')
            return redirect(url_for('president.clear_data_page'))
        
        try:
            # Count records before deletion
            contrib_count = db.session.query(Contribution).count()
            loans_count = db.session.query(Loan).count()
            trans_count = db.session.query(Transaction).count()
            summary_count = db.session.query(MonthlySummary).count()
            total_records = contrib_count + loans_count + trans_count + summary_count
            
            # Store data for audit log
            client_ip = request.remote_addr
            
            # Delete all transactional data
            db.session.query(Contribution).delete()
            db.session.query(Loan).delete()
            db.session.query(Transaction).delete()
            db.session.query(MonthlySummary).delete()
            
            # Create audit log entry
            audit = AuditLog(
                action='database_cleared',
                performed_by=current_user.id,
                description=f'Nettoyage complet des données par {current_user.full_name}',
                affected_records=total_records,
                details=f'Contributions: {contrib_count}, Loans: {loans_count}, Transactions: {trans_count}, Summaries: {summary_count}',
                ip_address=client_ip
            )
            db.session.add(audit)
            db.session.commit()
            
            flash(f'✓ Base de données nettoyée! {total_records} enregistrements supprimés. L\'historique d\'audit a été conservé.', 'success')
            return redirect(url_for('president.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'✗ Erreur lors du nettoyage: {str(e)}', 'error')
            return redirect(url_for('president.clear_data_page'))
    
    return render_template('president/clear_data.html')
