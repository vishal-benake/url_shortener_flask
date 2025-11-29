from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class URL(db.Model):
    __tablename__ = "urls"
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(32), unique=True, index=True, nullable=False)
    secret_key = db.Column(db.String(32), unique=True, index=True, nullable=False)
    target_url = db.Column(db.String(512), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    clicks = db.Column(db.Integer, default=0, nullable=False)
