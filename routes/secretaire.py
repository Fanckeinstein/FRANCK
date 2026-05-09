from flask import Blueprint, render_template, request, jsonify, send_file
from flask_login import login_required, current_user
from extensions import db
from models import User, Contribution, Loan, Transaction
from datetime import datetime
from sqlalchemy import func
import io
import csv


def _month_expr(col):
    """Return a SQL expression that extracts YYYY-MM from a datetime column in a DB-agnostic way."""
    try:
        dialect_name = (db.engine.dialect.name or '').lower()
    except Exception:
        dialect_name = 'sqlite'

    if 'sqlite' in dialect_name:
        return func.strftime('%Y-%m', col)
    if 'postgres' in dialect_name or 'postgresql' in dialect_name:
        return func.to_char(col, 'YYYY-MM')
    return func.to_char(col, 'YYYY-MM')

secretaire_bp = Blueprint('secretaire', __name__, url_prefix='/secretaire', template_folder='../templates')


@secretaire_bp.before_request
@login_required
def check_role():
    """Ensure only secretaries access this blueprint"""
    if current_user.role not in ['secretaire', 'president']:
        return jsonify({'error': 'Unauthorized'}), 403


@secretaire_bp.route('/dashboard')
def dashboard():
    """Secretary dashboard"""
    # Monthly report for current month
    current_month = datetime.utcnow().strftime('%Y-%m')
    
    # Contributions stats
    total_contributions = db.session.query(func.sum(Contribution.amount)).filter(
        Contribution.month == current_month,
        Contribution.status == 'paid'
    ).scalar() or 0
    
    contributions_paid = db.session.query(func.count(Contribution.id)).filter(
        Contribution.month == current_month,
        Contribution.status == 'paid'
    ).scalar()
    
    contributions_pending = db.session.query(func.count(Contribution.id)).filter(
        Contribution.month == current_month,
        Contribution.status.in_(['pending', 'overdue'])
    ).scalar()
    
    # Loans stats
    loans_approved = db.session.query(func.sum(Loan.amount)).filter_by(
        status='approved'
    ).scalar() or 0
    
    loans_count = db.session.query(func.count(Loan.id)).filter_by(
        status='pending'
    ).scalar()
    
    # Treasury balance
    total_all = db.session.query(func.sum(Contribution.amount)).filter_by(
        status='paid'
    ).scalar() or 0
    
    return render_template('secretaire/dashboard.html',
        current_month=current_month,
        total_contributions=float(total_contributions),
        contributions_paid=contributions_paid,
        contributions_pending=contributions_pending,
        loans_approved=float(loans_approved),
        loans_count=loans_count,
        treasury_balance=float(total_all) - float(loans_approved)
    )


@secretaire_bp.route('/monthly-report')
def monthly_report():
    """View monthly reports"""
    month_expr = _month_expr(Transaction.created_at)
    reports = db.session.query(month_expr).group_by(month_expr).all()
    
    return render_template('secretaire/monthly_report.html', reports=[r[0] for r in reports])


@secretaire_bp.route('/api/report/<month>')
@login_required
def get_report(month):
    """Get report for specific month"""
    if current_user.role not in ['secretaire', 'president']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Contributions
    contributions = db.session.query(
        func.count(Contribution.id),
        func.sum(Contribution.amount),
        Contribution.status
    ).filter_by(month=month).group_by(Contribution.status).all()
    
    # Loans
    loans_approved = db.session.query(func.count(Loan.id)).filter_by(
        status='approved'
    ).scalar()
    
    loans_pending = db.session.query(func.count(Loan.id)).filter_by(
        status='pending'
    ).scalar()
    
    # Treasury
    total_contrib = db.session.query(func.sum(Contribution.amount)).filter(
        Contribution.month == month,
        Contribution.status == 'paid'
    ).scalar() or 0
    
    total_loans = db.session.query(func.sum(Loan.amount)).filter_by(
        status='approved'
    ).scalar() or 0
    
    return jsonify({
        'month': month,
        'contributions': [
            {'status': c[2], 'count': c[0], 'amount': float(c[1] or 0)}
            for c in contributions
        ],
        'loans_approved': loans_approved,
        'loans_pending': loans_pending,
        'treasury_balance': float(total_contrib) - float(total_loans)
    })


@secretaire_bp.route('/history')
def history():
    """View complete transaction history"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    pagination = Transaction.query.order_by(
        Transaction.created_at.desc()
    ).paginate(page=page, per_page=per_page)
    
    return render_template('secretaire/history.html', pagination=pagination)


@secretaire_bp.route('/api/export/<format>')
@login_required
def export_report(format):
    """Export report in CSV or PDF"""
    if current_user.role not in ['secretaire', 'president']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    month = request.args.get('month', datetime.utcnow().strftime('%Y-%m'))
    
    if format == 'csv':
        # Generate CSV
        import csv
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['Transaction Type', 'User', 'Amount', 'Date', 'Description'])
        
        month_expr = _month_expr(Transaction.created_at)
        transactions = Transaction.query.filter(
            month_expr == month
        ).all()
        
        for t in transactions:
            user = User.query.get(t.user_id)
            writer.writerow([t.type, user.full_name, t.amount, t.created_at.isoformat(), t.description])
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'report_{month}.csv'
        )
    
    return jsonify({'error': 'Format not supported'}), 400


@secretaire_bp.route('/announcements')
def announcements():
    """View and manage announcements"""
    return render_template('secretaire/announcements.html')
