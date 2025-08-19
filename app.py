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
    return redirect("/") 

# Homepage (Dashboard)
@app.route("/")
def homepage():
    # Example: get user balance and recent transactions (static user for now)
    user_id = 1  # Placeholder, will use session later
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    balance = user[0]["cash"] if user else 0
    transactions = db.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC LIMIT 5", user_id)
    return render_template("dashboard.html", balance=balance, transactions=transactions)
def homepage():
    return render_template("homepage.html")
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

