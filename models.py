from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


db = SQLAlchemy()

class URL(db.Model):
    __tablename__ = "urls"
    id = db.Column(db.Integer, primary_key=True)
    shorten_key = db.Column(db.String(32), unique=True, index=True, nullable=False)
    secret_key = db.Column(db.String(32), unique=True, index=True, nullable=False)
    target_url = db.Column(db.String(512), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    status = db.Column(db.String(10), default='active')  # 'active' or 'deactivated'
    clicks = db.Column(db.Integer, default=0, nullable=False)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="operator")  # 'admin' or 'operator'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Referral(db.Model):
    __tablename__ = "referrals"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), unique=True, nullable=False, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used_at = db.Column(db.DateTime, nullable=True)

class ReferralHistory(db.Model):
    __tablename__ = "referral_history"
    id = db.Column(db.Integer, primary_key=True)
    referral_id = db.Column(db.Integer, db.ForeignKey('referrals.id'), nullable=False)
    used_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    ip_address = db.Column(db.String(100))
    user_agent = db.Column(db.String(512))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class ActionLog(db.Model):
    __tablename__ = "action_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(128), nullable=False)
    details = db.Column(db.String(1024))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
