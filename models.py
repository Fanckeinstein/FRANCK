from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

class User(db.Model, UserMixin):
    """User model for Unissons la Main members and admins"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    
    # Role: 'president', 'tresorier', 'secretaire', 'member'
    role = db.Column(db.String(20), default='member', nullable=False)
    
    is_active = db.Column(db.Boolean, default=False)  # Inactive until email verified
    profile_pic = db.Column(db.String(300), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class VerificationCode(db.Model):
    """Verification codes for email/WhatsApp signup"""
    __tablename__ = 'verification_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    code = db.Column(db.String(10), nullable=False)
    purpose = db.Column(db.String(50), default='register')  # 'register', 'reset', etc
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', foreign_keys=[user_id])


class Contribution(db.Model):
    """Monthly contribution record (1000 FCFA per member)"""
    __tablename__ = 'contributions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, default=1000.0)  # FCFA
    month = db.Column(db.String(7), nullable=False)  # Format: 'YYYY-MM'
    status = db.Column(db.String(20), default='pending')  # 'pending', 'paid', 'overdue'
    payment_method = db.Column(db.String(50), nullable=True)  # 'mobile_money', 'cash', 'bank'
    payment_proof = db.Column(db.String(300), nullable=True)  # Path to screenshot/receipt
    paid_at = db.Column(db.DateTime, nullable=True)
    validated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id])
    validator = db.relationship('User', foreign_keys=[validated_by])


class Loan(db.Model):
    """Emergency loan requests"""
    __tablename__ = 'loans'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)  # FCFA requested
    reason = db.Column(db.String(500), nullable=False)  # Urgency explanation
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected', 'repaid'
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approval_notes = db.Column(db.String(500), nullable=True)
    repayment_deadline = db.Column(db.DateTime, nullable=True)
    amount_repaid = db.Column(db.Float, default=0.0)
    repaid_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', foreign_keys=[user_id])
    approver = db.relationship('User', foreign_keys=[approved_by])


class Transaction(db.Model):
    """Audit log of all financial transactions"""
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # 'contribution', 'loan_approved', 'repayment', etc
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reference_id = db.Column(db.Integer, nullable=True)  # contribution_id, loan_id, etc

    user = db.relationship('User', foreign_keys=[user_id])


class MonthlySummary(db.Model):
    """Auto-generated monthly financial summary (10th of each month)"""
    __tablename__ = 'monthly_summaries'
    
    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.String(7), unique=True, nullable=False)  # Format: 'YYYY-MM'
    total_collected = db.Column(db.Float, default=0.0)
    total_loans_approved = db.Column(db.Float, default=0.0)
    total_repaid = db.Column(db.Float, default=0.0)
    fund_balance = db.Column(db.Float, default=0.0)
    members_paid = db.Column(db.Integer, default=0)
    members_pending = db.Column(db.Integer, default=0)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    published_at = db.Column(db.DateTime, nullable=True)
