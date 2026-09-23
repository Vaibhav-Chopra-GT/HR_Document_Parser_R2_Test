from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import secrets
import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

db = SQLAlchemy()

# Encryption key derivation from SECRET_KEY
_fernet = None

def get_fernet():
    """Get or create Fernet instance for encryption"""
    global _fernet
    if _fernet is None:
        from flask import current_app
        secret = current_app.config.get('SECRET_KEY', 'default-secret-key')
        # Derive a proper Fernet key from SECRET_KEY
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'talently_salt_v1',  # Fixed salt for consistent key derivation
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
        _fernet = Fernet(key)
    return _fernet

def encrypt_data(data: str) -> str:
    """Encrypt sensitive data"""
    if not data:
        return data
    return get_fernet().encrypt(data.encode()).decode()

def decrypt_data(encrypted: str) -> str:
    """Decrypt sensitive data"""
    if not encrypted:
        return encrypted
    try:
        return get_fernet().decrypt(encrypted.encode()).decode()
    except:
        return encrypted  # Return as-is if decryption fails (legacy data)


def generate_uuid():
    return str(uuid.uuid4())


def generate_token():
    return secrets.token_urlsafe(32)


class User(db.Model):
    """HR User model"""
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(255))  # Organization/Company name

    # Status
    is_active = db.Column(db.Boolean, default=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)

    # Relationships
    candidates = db.relationship('Candidate', backref='owner', lazy='dynamic')

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'company': self.company,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None
        }


class Candidate(db.Model):
    """Candidate model with extracted resume data"""
    __tablename__ = 'candidates'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)

    # Owner (HR User)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)  # nullable for migration

    # Extracted Information
    name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    company = db.Column(db.String(255))
    designation = db.Column(db.String(255))
    skills = db.Column(db.Text)  # JSON array stored as string
    raw_resume_text = db.Column(db.Text)

    # Confidence Scores (0.0 - 1.0)
    name_confidence = db.Column(db.Float)
    email_confidence = db.Column(db.Float)
    phone_confidence = db.Column(db.Float)
    company_confidence = db.Column(db.Float)
    designation_confidence = db.Column(db.Float)
    skills_confidence = db.Column(db.Float)
    overall_confidence = db.Column(db.Float)

    # File References
    resume_filename = db.Column(db.String(500))
    resume_original_name = db.Column(db.String(500))
    pan_filename = db.Column(db.String(500))
    pan_original_name = db.Column(db.String(500))
    aadhaar_filename = db.Column(db.String(500))
    aadhaar_original_name = db.Column(db.String(500))

    # Document Validation
    pan_validated = db.Column(db.Boolean, default=False)
    aadhaar_validated = db.Column(db.Boolean, default=False)

    # Status Tracking
    extraction_status = db.Column(db.String(50), default='pending')  # pending, processing, completed, failed
    extraction_error = db.Column(db.Text)
    document_status = db.Column(db.String(50), default='pending')  # pending, requested, partial, completed

    # Secure Portal Access
    submission_token = db.Column(db.String(100), unique=True)
    token_expires_at = db.Column(db.DateTime)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    documents_requested_at = db.Column(db.DateTime)
    documents_submitted_at = db.Column(db.DateTime)

    # Relationships (cascade delete so logs are removed when candidate is deleted)
    audit_logs = db.relationship('AuditLog', backref='candidate', lazy='dynamic', cascade='all, delete-orphan')
    email_logs = db.relationship('EmailLog', backref='candidate', lazy='dynamic', cascade='all, delete-orphan')

    def generate_submission_token(self, expiry_days=None):
        """Generate a new submission token. If expiry_days is None, link never expires."""
        self.submission_token = generate_token()
        if expiry_days:
            self.token_expires_at = datetime.utcnow() + timedelta(days=expiry_days)
        else:
            self.token_expires_at = None  # Never expires
        return self.submission_token

    def is_token_valid(self):
        """Check if submission token is still valid"""
        if not self.submission_token:
            return False
        # If no expiry set, token is always valid
        if not self.token_expires_at:
            return True
        return datetime.utcnow() < self.token_expires_at

    def to_dict(self, include_sensitive=False):
        """Convert to dictionary for API response"""
        data = {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'company': self.company,
            'designation': self.designation,
            'skills': self.skills,
            'confidence_scores': {
                'name': self.name_confidence,
                'email': self.email_confidence,
                'phone': self.phone_confidence,
                'company': self.company_confidence,
                'designation': self.designation_confidence,
                'skills': self.skills_confidence,
                'overall': self.overall_confidence
            },
            'extraction_status': self.extraction_status,
            'extraction_error': self.extraction_error,
            'document_status': self.document_status,
            'has_pan': bool(self.pan_filename),
            'has_aadhaar': bool(self.aadhaar_filename),
            'pan_validated': self.pan_validated,
            'aadhaar_validated': self.aadhaar_validated,
            'resume_original_name': self.resume_original_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'documents_requested_at': self.documents_requested_at.isoformat() if self.documents_requested_at else None,
            'documents_submitted_at': self.documents_submitted_at.isoformat() if self.documents_submitted_at else None
        }

        if include_sensitive:
            data['submission_token'] = self.submission_token
            data['token_expires_at'] = self.token_expires_at.isoformat() if self.token_expires_at else None

        return data

    def to_list_dict(self):
        """Simplified dict for list view"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'company': self.company,
            'extraction_status': self.extraction_status,
            'document_status': self.document_status,
            'overall_confidence': self.overall_confidence,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AuditLog(db.Model):
    """Immutable audit log for compliance"""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    candidate_id = db.Column(db.String(36), db.ForeignKey('candidates.id'))
    action = db.Column(db.String(100), nullable=False)
    actor = db.Column(db.String(50))  # 'system', 'hr', 'candidate'
    actor_ip = db.Column(db.String(50))
    details = db.Column(db.Text)  # JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'action': self.action,
            'actor': self.actor,
            'details': self.details,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class EmailLog(db.Model):
    """Email tracking log"""
    __tablename__ = 'email_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    candidate_id = db.Column(db.String(36), db.ForeignKey('candidates.id'), nullable=False)
    email_type = db.Column(db.String(50), nullable=False)  # document_request, reminder, confirmation
    recipient_email = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(500))
    body_preview = db.Column(db.String(500))
    status = db.Column(db.String(50), default='pending')  # pending, sent, delivered, failed, bounced
    resend_message_id = db.Column(db.String(100))
    sent_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'email_type': self.email_type,
            'recipient_email': self.recipient_email,
            'subject': self.subject,
            'status': self.status,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'error_message': self.error_message
        }
