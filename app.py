from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp
# Flask-WTF configuration
app.config['WTF_CSRF_ENABLED'] = True

# Rate limiting configuration (by IP and username)
RATE_LIMIT_ATTEMPTS = 5
RATE_LIMIT_WINDOW = 300  # 5 minutes in seconds
login_attempts = {}  # {ip: [timestamps], username: [timestamps]}

# Flask-WTF LoginForm
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50), Regexp(r'^[a-zA-Z0-9_.-]+$')])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

def check_rate_limit(ip_address, username=None):
    import time
    current_time = time.time()
    # Clean old entries for IP
    if ip_address in login_attempts:
        login_attempts[ip_address] = [t for t in login_attempts[ip_address] if current_time - t < RATE_LIMIT_WINDOW]
    # Clean old entries for username
    if username and username in login_attempts:
        login_attempts[username] = [t for t in login_attempts[username] if current_time - t < RATE_LIMIT_WINDOW]
    # Check rate limit for IP
    if ip_address in login_attempts and len(login_attempts[ip_address]) >= RATE_LIMIT_ATTEMPTS:
        raise Exception(f"Too many login attempts from this IP. Please try again in {RATE_LIMIT_WINDOW // 60} minutes.")
    # Check rate limit for username
    if username and username in login_attempts and len(login_attempts[username]) >= RATE_LIMIT_ATTEMPTS:
        raise Exception(f"Too many login attempts for this user. Please try again in {RATE_LIMIT_WINDOW // 60} minutes.")

def record_login_attempt(ip_address, username=None):
    import time
    current_time = time.time()
    if ip_address not in login_attempts:
        login_attempts[ip_address] = []
    login_attempts[ip_address].append(current_time)
    if username:
        if username not in login_attempts:
            login_attempts[username] = []
        login_attempts[username].append(current_time)

def validate_credentials(username, password):
    import re
    # Input validation
    if not username or not password:
        raise Exception("Username and password are required.")
    if not re.match(r'^[a-zA-Z0-9_.-]+$', username) or len(username) < 3 or len(username) > 50:
        raise Exception("Invalid username format.")
    # Password complexity
    if len(password) < 8 or not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password) or not re.search(r'[0-9]', password) or not re.search(r'[^A-Za-z0-9]', password):
        raise Exception("Password must be at least 8 characters and include uppercase, lowercase, digit, and special character.")
    # Query user from database
    user = db.execute('SELECT * FROM users WHERE username = ?', username)
    if not user:
        return False
    from werkzeug.security import check_password_hash
    if not check_password_hash(user[0]['password_hash'], password):
        return False
    return user[0]['id']

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if form.validate_on_submit():
        try:
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            if ',' in client_ip:
                client_ip = client_ip.split(',')[0].strip()
            username = form.username.data.strip()
            password = form.password.data
            remember_me = form.remember_me.data
            check_rate_limit(client_ip, username)
            record_login_attempt(client_ip, username)
            user_id = validate_credentials(username, password)
            if user_id:
                session.clear()
                session['user_id'] = user_id
                session['login_time'] = datetime.now().isoformat()
                session['ip_address'] = client_ip
                session.permanent = remember_me
                # Clear rate limiting for successful login
                if client_ip in login_attempts:
                    del login_attempts[client_ip]
                if username in login_attempts:
                    del login_attempts[username]
                flash('Login successful!', 'success')
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password.', 'error')
        except Exception as e:
            flash(str(e), 'error')
            return render_template('login.html', form=form), 429
    return render_template('login.html', form=form)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    flash('You have been successfully logged out.', 'info')
    return redirect(url_for('login'))
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from cs50 import SQL 
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
from helpers import apology, login_required

# Initialize Flask app
app = Flask(__name__)

# Configure Flask session
app.secret_key = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this-in-production'
app.permanent_session_lifetime = timedelta(days=7)  # Session expires after 7 days

# Optional: Configure session settings
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to cookies
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection

# Configure Flask-Session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Create the database
db = SQL("sqlite:///database.db")

def init_db():
    """Initialise la base de données avec les tables nécessaires"""
    
    # Table utilisateurs
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT,
            google_id TEXT,
            oauth_provider TEXT,
            cash NUMERIC NOT NULL DEFAULT 10000.00,
            theme TEXT DEFAULT 'light',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table catégories
    db.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT CHECK(type IN ('income', 'expense')) NOT NULL
        )
    ''')
    
    # Table transactions
    db.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER,
            amount NUMERIC NOT NULL,
            currency TEXT DEFAULT 'USD',
            description TEXT,
            date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
        )
    ''')
    
    # Table budgets
    db.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER,
            amount NUMERIC NOT NULL,
            period TEXT CHECK(period IN ('weekly', 'monthly', 'yearly')) NOT NULL,
            start_date DATE NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')
    
    # Table objectifs d'épargne
    db.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            target_amount NUMERIC NOT NULL,
            current_amount NUMERIC DEFAULT 0,
            deadline DATE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # Index pour optimiser les requêtes
    db.execute('CREATE INDEX IF NOT EXISTS idx_txn_user_date ON transactions(user_id, date DESC)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_txn_category ON transactions(category_id)')
    
    # Insérer des catégories par défaut
    default_categories = [
        ('Food & Dining', 'expense'),
        ('Transportation', 'expense'),
        ('Shopping', 'expense'),
        ('Entertainment', 'expense'),
        ('Bills & Utilities', 'expense'),
        ('Healthcare', 'expense'),
        ('Salary', 'income'),
        ('Freelance', 'income'),
        ('Investments', 'income'),
        ('Other Income', 'income')
    ]
    
    for name, cat_type in default_categories:
        db.execute('INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)', 
                  name, cat_type)

#login
@app.route("/login", methods = ["GET", "POST"])
def login():
    return redirect("/dashboard") 
# Homepage (Dashboard)
@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def homepage():
    # Example: get user balance and recent transactions (static user for now)
    user_id = 1  # Placeholder, will use session later
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    balance = user[0]["cash"] if user else 0
    transactions = db.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC LIMIT 5", user_id)
    return render_template("dashboard.html", balance=balance, transactions=transactions)

#transaction
@app.route("/transactions", methods = ["GET", "POST"])
@login_required
def transaction():
    return render_template("transaction.html")
#budget
@app.route("/budget", methods = ["GET", "POST"])
@login_required
def budget():
    return render_template("budget.html")
#profile
@app.route("/profile", methods = ["GET", "POST"])
@login_required
def profile():
    return render_template("profile.html")
#logout
@app.route("/logout", methods = ["GET", "POST"])
@login_required
def logout():
    return redirect(url_for("login"))

if __name__ == '__main__':

    # Initialiser la base de données au démarrage
    init_db()
    
    # Lancer l'application
    app.run(debug=True, host="0.0.0.0", port=5000)

