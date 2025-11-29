# app.py
import os
import string
import random
from datetime import datetime
from functools import lru_cache, wraps

from flask import (
    Flask, request, render_template, redirect, url_for, flash, session, jsonify
)
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user, UserMixin
)
from werkzeug.security import generate_password_hash, check_password_hash
import validators

from config import Config
from models import db, URL, User, Referral, ReferralHistory, ActionLog

from werkzeug.security import generate_password_hash

# ---- App setup ----
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

# ---- Create DB ----
with app.app_context():
    db.create_all()

    admin_username = "Vishal"
    admin_password = "MonsterHost8767"

    existing_admin = User.query.filter_by(username=admin_username).first()

    if not existing_admin:
        hashed_pass = generate_password_hash(admin_password)
        new_admin = User(
            username=admin_username,
            password_hash=hashed_pass,
            role="admin"
        )
        db.session.add(new_admin)
        db.session.commit()
        print("Default admin created: vishal")
    else:
        print("Admin already exists")

# ---- Helper: user class for Flask-Login ----
class UserModel(UserMixin):
    def __init__(self, user):
        self.user = user

    def get_id(self):
        return str(self.user.id)

    @property
    def is_active(self):
        return True

    @property
    def username(self):
        return self.user.username

    @property
    def role(self):
        return self.user.role

@login_manager.user_loader
def load_user(user_id):
    u = User.query.get(int(user_id))
    return UserModel(u) if u else None

# ---- Utility functions ----
def log_action(user_id, action, details=None):
    a = ActionLog(user_id=user_id, action=action, details=(details or "")[:1000])
    db.session.add(a)
    db.session.commit()

def generate_key(n=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=n))

def generate_unique_shorten_key():
    while True:
        key = generate_key(6)
        if not URL.query.filter_by(shorten_key=key).first():
            return key

def generate_secret_key():
    return generate_key(12)

def generate_referral_code(n=8):
    chars = string.ascii_uppercase + string.digits
    while True:
        c = ''.join(random.choices(chars, k=n))
        if not Referral.query.filter_by(code=c).first():
            return c

# LRU cache for fast lookup
@lru_cache(maxsize=2048)
def get_url_by_key(url_key):
    return URL.query.filter_by(shorten_key=url_key, is_active=True).first()

def clear_url_cache():
    get_url_by_key.cache_clear()

# Role check decorator
def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            # load underlying DB user
            u = User.query.get(int(current_user.get_id()))
            if u.role not in roles:
                flash("Unauthorized", "warning")
                return redirect(url_for('index'))
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# ---- Routes ----

@app.route('/', methods=['GET', 'POST'])
def index():
    short_url = None
    if request.method == 'POST':
        target_url = request.form.get('target_url', '').strip()
        if not validators.url(target_url):
            flash("Invalid URL! Please enter a valid URL (including http/https).", "danger")
        else:
            url_key = generate_unique_shorten_key()
            secret_key = generate_secret_key()
            new_url = URL(shorten_key=url_key, secret_key=secret_key, target_url=target_url)
            db.session.add(new_url)
            db.session.commit()
            clear_url_cache()
            short_url = f"{Config.BASE_URL}/{url_key}"
            # log if user is authenticated
            uid = int(current_user.get_id()) if current_user.is_authenticated else None
            log_action(uid, "create_url", f"{short_url} -> {target_url}")
    return render_template("index.html", short_url=short_url)

@app.route('/<string:url_key>')
def redirect_short(url_key):
    # case-sensitive exact match; adjust if needed
    url = get_url_by_key(url_key)
    if not url:
        return render_template("404.html"), 404
    url.clicks = (url.clicks or 0) + 1
    db.session.commit()
    # log click anonymously (no user)
    log_action(None, "redirect", f"key={url_key} to {url.target_url}")
    return redirect(url.target_url)

# ----- Authentication -----
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(UserModel(user))
            flash("Logged in successfully.", "success")
            log_action(user.id, "login", f"user {username} logged in")
            return redirect(url_for('admin_panel'))
        else:
            flash("Invalid credentials.", "danger")
    return render_template("login.html")

@app.route('/logout')
@login_required
def logout():
    uid = int(current_user.get_id())
    logout_user()
    flash("Logged out.", "success")
    log_action(uid, "logout", "user logged out")
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        referral_code = request.form.get('referral','').strip()
        if not username or not password:
            flash("Username and password required.", "warning")
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "warning")
            return redirect(url_for('register'))

        # Check referral if provided
        used_referral = None
        if referral_code:
            ref = Referral.query.filter_by(code=referral_code).first()
            if not ref:
                flash("Invalid referral code.", "warning")
                return redirect(url_for('register'))
            if ref.is_used:
                flash("Referral code already used.", "warning")
                return redirect(url_for('register'))
            used_referral = ref

        # create user
        hashed = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed, role="operator")
        db.session.add(new_user)
        db.session.commit()

        # Mark referral used and store history
        if used_referral:
            used_referral.is_used = True
            used_referral.used_at = datetime.utcnow()
            db.session.commit()
            rh = ReferralHistory(
                referral_id=used_referral.id,
                used_by_user_id=new_user.id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(rh)
            db.session.commit()

        log_action(new_user.id, "register", f"registered with referral={referral_code or 'none'}")
        login_user(UserModel(new_user))
        flash("Account created and logged in.", "success")
        return redirect(url_for('admin_panel'))
    return render_template('register.html')

# ----- Admin panel & account manager -----
@app.route('/admin')
@login_required
@role_required('admin','operator')
def admin_panel():
    # admins see everything; operators see limited info
    urls = URL.query.order_by(URL.id.desc()).all()
    referrals = Referral.query.order_by(Referral.created_at.desc()).all() if current_user.user.role == 'admin' else Referral.query.filter_by(created_by=int(current_user.get_id())).all()
    users = User.query.order_by(User.id.desc()).all() if current_user.user.role == 'admin' else []
    return render_template('admin.html', urls=urls, referrals=referrals, users=users, current_role=current_user.user.role)

# Create referral (admin or operator)
@app.route('/admin/create_referral', methods=['POST'])
@login_required
@role_required('admin','operator')
def create_referral():
    code = generate_referral_code()
    created_by = int(current_user.get_id())
    r = Referral(code=code, created_by=created_by)
    db.session.add(r)
    db.session.commit()
    log_action(created_by, "create_referral", f"code={code}")
    flash(f"Referral {code} created.", "success")
    return redirect(url_for('admin_panel'))

# Deactivate URL
@app.route('/admin/deactivate/<int:url_id>', methods=['POST'])
@login_required
@role_required('admin','operator')
def deactivate_url(url_id):
    url = URL.query.get_or_404(url_id)
    url.is_active = False
    db.session.commit()
    clear_url_cache()
    uid = int(current_user.get_id())
    log_action(uid, "deactivate_url", f"id={url.id} key={url.shorten_key}")
    flash(f"URL {url.shorten_key} deactivated.", "warning")
    return redirect(url_for('admin_panel'))

# Reactivate URL
@app.route('/admin/reactivate/<int:url_id>', methods=['POST'])
@login_required
@role_required('admin','operator')
def reactivate_url(url_id):
    url = URL.query.get_or_404(url_id)
    url.is_active = True
    db.session.commit()
    clear_url_cache()
    uid = int(current_user.get_id())
    log_action(uid, "reactivate_url", f"id={url.id} key={url.shorten_key}")
    flash(f"URL {url.shorten_key} reactivated.", "success")
    return redirect(url_for('admin_panel'))

# Delete selected
@app.route('/admin/delete_selected', methods=['POST'])
@login_required
@role_required('admin')
def delete_selected():
    selected_ids = request.form.getlist('selected_urls')
    if not selected_ids:
        flash("No URLs selected!", "warning")
        return redirect(url_for('admin_panel'))
    # convert to ints
    ids = [int(x) for x in selected_ids]
    deleted = URL.query.filter(URL.id.in_(ids)).all()
    count = len(deleted)
    for d in deleted:
        db.session.delete(d)
    db.session.commit()
    clear_url_cache()
    log_action(int(current_user.get_id()), "delete_selected", f"ids={ids}")
    flash(f"Deleted {count} selected URLs.", "success")
    return redirect(url_for('admin_panel'))

# Delete all deactivated
@app.route('/admin/delete_deactivated', methods=['POST'])
@login_required
@role_required('admin')
def delete_deactivated():
    deactivated = URL.query.filter_by(is_active=False).all()
    if not deactivated:
        flash("No deactivated URLs to delete!", "warning")
        return redirect(url_for('admin_panel'))
    count = len(deactivated)
    for r in deactivated:
        db.session.delete(r)
    db.session.commit()
    clear_url_cache()
    log_action(int(current_user.get_id()), "delete_deactivated", f"count={count}")
    flash(f"Deleted {count} deactivated URLs.", "success")
    return redirect(url_for('admin_panel'))

# Create user (admin only) - to add admin/operator accounts
@app.route('/admin/create_user', methods=['POST'])
@login_required
@role_required('admin')
def create_user():
    username = request.form.get('username','').strip()
    password = request.form.get('password','')
    role = request.form.get('role','operator')
    if not username or not password:
        flash("Username and password required.", "warning")
        return redirect(url_for('admin_panel'))
    if User.query.filter_by(username=username).first():
        flash("Username exists.", "warning")
        return redirect(url_for('admin_panel'))
    h = generate_password_hash(password)
    u = User(username=username, password_hash=h, role=role)
    db.session.add(u)
    db.session.commit()
    log_action(int(current_user.get_id()), "create_user", f"user={username} role={role}")
    flash("User created.", "success")
    return redirect(url_for('admin_panel'))

# View action logs (admin)
@app.route('/admin/logs')
@login_required
@role_required('admin')
def view_logs():
    logs = ActionLog.query.order_by(ActionLog.timestamp.desc()).limit(200).all()
    return render_template('logs.html', logs=logs)

@app.route('/admin/referral_history')
@login_required
@role_required('admin')
def ref_History():
    # Fetch referral history with user and referral info
    history = db.session.query(
        ReferralHistory,
        Referral.code.label("referral_code"),
        User.username.label("used_by")
    ).join(
        Referral, Referral.id == ReferralHistory.referral_id
    ).outerjoin(
        User, User.id == ReferralHistory.used_by_user_id
    ).order_by(ReferralHistory.timestamp.desc()).all()
    
    return render_template('referral_history.html', history=history)

# ---- Error handlers ----
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# ---- Run ----
if __name__ == "__main__":
    app.run(debug=True)
