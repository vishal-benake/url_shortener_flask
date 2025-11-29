# app.py
from flask import Flask, request, render_template, redirect, url_for, flash
from config import Config
from models import db, URL
import string, random, validators
from functools import lru_cache

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY
db.init_app(app)

with app.app_context():
    db.create_all()

# ----- Helper Functions -----
def generate_key(n=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=n))

def generate_unique_key():
    while True:
        key = generate_key()
        if not URL.query.filter_by(shorten_key=key).first():
            return key

def generate_secret_key():
    return generate_key(12)

# LRU Cache for redirect
@lru_cache(maxsize=1024)
def get_url_by_key(url_key):
    return URL.query.filter_by(shorten_key=url_key, is_active=True).first()

# ----- Routes -----
@app.route('/', methods=['GET', 'POST'])
def index():
    short_url = None
    if request.method == 'POST':
        target_url = request.form.get('target_url')
        if not validators.url(target_url):
            flash("Invalid URL! Please enter a valid URL.", "danger")
        else:
            url_key = generate_unique_key()
            secret_key = generate_secret_key()
            new_url = URL(shorten_key=url_key, secret_key=secret_key, target_url=target_url)
            db.session.add(new_url)
            db.session.commit()
            short_url = f"{Config.BASE_URL}/{url_key}"
    return render_template("index.html", short_url=short_url)

@app.route('/<string:url_key>')
def redirect_short(url_key):
    url = get_url_by_key(url_key)
    if not url:
        return render_template("404.html"), 404
    url.clicks += 1
    db.session.commit()
    return redirect(url.target_url)

@app.route('/admin')
def admin_panel():
    urls = URL.query.order_by(URL.id.desc()).all()
    return render_template("admin.html", urls=urls)

@app.route('/admin/deactivate/<int:url_id>')
def deactivate_url(url_id):
    url = URL.query.get_or_404(url_id)
    url.is_active = False
    db.session.commit()
    get_url_by_key.cache_clear()  # Clear cache to reflect deactivation
    flash(f"URL {url.shorten_key} deactivated.", "warning")
    return redirect(url_for('admin_panel'))

@app.route("/admin/reactivate/<int:url_id>", methods=["POST"])
def reactivate_url(url_id):
    url = URL.query.get_or_404(url_id)
    if url.is_active:
        flash("URL is already active!", "warning")
    else:
        url.is_active = True
        db.session.commit()
        get_url_by_key.cache_clear()  # IMPORTANT FIX
        flash(f"URL {url.shorten_key} reactivated successfully!", "success")
    return redirect(url_for("admin_panel"))

@app.route("/admin/delete_selected", methods=["POST"])
def delete_selected():
    selected_ids = request.form.getlist("selected_urls")
    if not selected_ids:
        flash("No URLs selected!", "warning")
        return redirect(url_for("admin_panel"))
    URL.query.filter(URL.id.in_(selected_ids)).delete(synchronize_session=False)
    db.session.commit()
    flash(f"Deleted {len(selected_ids)} selected URLs!", "success")
    return redirect(url_for("admin_panel"))

@app.route("/admin/delete_deactivated", methods=["POST"])
def delete_deactivated():
    deactivated_urls = URL.query.filter_by(is_active=False).all()
    if not deactivated_urls:
        flash("No deactivated URLs to delete!", "warning")
        return redirect(url_for("admin_panel"))
    for url in deactivated_urls:
        db.session.delete(url)
    db.session.commit()
    flash(f"Deleted {len(deactivated_urls)} deactivated URLs!", "success")
    return redirect(url_for("admin_panel"))

if __name__ == "__main__":
    app.run(debug=True)
