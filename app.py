
from flask_wtf import FlaskForm
from dotenv import load_dotenv
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp, Email, EqualTo
import re
import os
import logging
import time
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from cs50 import SQL 
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
from helpers import apology, login_required
import hashlib
import urllib.parse
from services import AuthService, UserService
from flask_wtf.csrf import generate_csrf
from decimal import Decimal, InvalidOperation

# --- Robust database initialization from database setup.md ---
import sqlite3
import threading
from pathlib import Path

class DatabaseInitializer:
    def __init__(self, db_path):
        self.db_path = Path(db_path).resolve()
        self._init_lock = threading.Lock()
        self._initialized = False
    def initialize_database(self):
        if self._initialized:
            return
        with self._init_lock:
            if self._initialized:
                return
            self._ensure_database_file_exists()
            self._create_schema()
            self._initialized = True
    def _ensure_database_file_exists(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.db_path.exists():
            conn = sqlite3.connect(str(self.db_path))
            conn.close()
    def _create_schema(self):
        conn = sqlite3.connect(str(self.db_path))
        try:
            with conn:
                # Users table
                conn.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token TEXT,
    email_verification_expires TIMESTAMP,
    password_reset_token TEXT,
    password_reset_expires TIMESTAMP,
    google_id TEXT,
    oauth_provider TEXT,
    cash NUMERIC NOT NULL DEFAULT 10000.00,
    theme TEXT DEFAULT 'light',
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP NULL,
    last_login TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
                ''')
                # Categories table
                conn.execute('''
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    type TEXT CHECK(type IN ('income', 'expense')) NOT NULL
)
                ''')
                # Transactions table
                conn.execute('''
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
                # Budgets table
                conn.execute('''
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
                # Goals table
                conn.execute('''
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
                # Security audit log table
                conn.execute('''
CREATE TABLE IF NOT EXISTS security_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    event_type TEXT NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
                ''')
                # Email verification attempts table
                conn.execute('''
CREATE TABLE IF NOT EXISTS email_verification_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    ip_address TEXT,
    attempts INTEGER DEFAULT 1,
    last_attempt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    blocked_until TIMESTAMP
)
                ''')
                # Indexes for optimization
                conn.execute('CREATE INDEX IF NOT EXISTS idx_txn_user_date ON transactions(user_id, date DESC)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_txn_category ON transactions(category_id)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_security_logs_user ON security_logs(user_id, timestamp)')
        finally:
            conn.close()

def get_database_path():
    if os.environ.get('FLASK_ENV') == 'production':
        return Path('/var/data/fintrack/fintrack.db')
    else:
        return Path(__file__).parent / 'instance' / 'fintrack.db'

DATABASE_PATH = get_database_path()
initializer = DatabaseInitializer(DATABASE_PATH)
initializer.initialize_database()
# --- End robust database initialization ---

# Configure logging for security events
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('security.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


load_dotenv()
# --- Robust database initialization (from database setup.md) ---
import sqlite3
from pathlib import Path

# Use absolute path for database
db_dir = Path(__file__).parent / "instance"
db_dir.mkdir(parents=True, exist_ok=True)
db_path = db_dir / "fintrack.db"

# Create database file and schema if needed
if not db_path.exists():
    conn = sqlite3.connect(str(db_path))
    with conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Add other tables as needed, e.g. transactions, categories, etc.
    conn.close()
# --- End robust database initialization ---


# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['REGISTRATION_ENABLED'] = True  # Allow registration by default
# --- Load mail config from environment ---
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', '1', 'yes']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

# Initialize database connection (after robust init)
db = SQL(f"sqlite:///{DATABASE_PATH}")

# Instantiate service classes with required dependencies
user_service = UserService(db)
auth_service = AuthService(user_service)

# Enhanced Flask session configuration for production
def init_db():
    """Initialize the database with necessary tables"""
    # Users table
    db.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token TEXT,
    email_verification_expires TIMESTAMP,
    password_reset_token TEXT,
    password_reset_expires TIMESTAMP,
    google_id TEXT,
    oauth_provider TEXT,
    cash NUMERIC NOT NULL DEFAULT 10000.00,
    theme TEXT DEFAULT 'light',
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP NULL,
    last_login TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
    # Categories table
    db.execute('''
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    type TEXT CHECK(type IN ('income', 'expense')) NOT NULL
)
''')
    # Transactions table
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
    # Budgets table
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
    # Goals table
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
    # Security audit log table
    db.execute('''
CREATE TABLE IF NOT EXISTS security_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    event_type TEXT NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
''')
    # Email verification attempts table
    db.execute('''
CREATE TABLE IF NOT EXISTS email_verification_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    ip_address TEXT,
    attempts INTEGER DEFAULT 1,
    last_attempt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    blocked_until TIMESTAMP
)
''')
    # Indexes for optimization
    db.execute('CREATE INDEX IF NOT EXISTS idx_txn_user_date ON transactions(user_id, date DESC)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_txn_category ON transactions(category_id)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_security_logs_user ON security_logs(user_id, timestamp)')
    # Insert default categories
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
        db.execute('INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)', name, cat_type)
    
    # Categories table
    db.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT CHECK(type IN ('income', 'expense')) NOT NULL
        )
    ''')
    
    # Transactions table
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
    
    # Budgets table
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
    
    # Goals table
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
    
    # Security audit log table
    db.execute('''
        CREATE TABLE IF NOT EXISTS security_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            event_type TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Email verification attempts table
    db.execute('''
        CREATE TABLE IF NOT EXISTS email_verification_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            ip_address TEXT,
            attempts INTEGER DEFAULT 1,
            last_attempt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            blocked_until TIMESTAMP
        )
    ''')
    
    # Indexes for optimization
    db.execute('CREATE INDEX IF NOT EXISTS idx_txn_user_date ON transactions(user_id, date DESC)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_txn_category ON transactions(category_id)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_security_logs_user ON security_logs(user_id, timestamp)')
    
    # Insert default categories
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

# Rate limiting configuration
RATE_LIMIT_ATTEMPTS = 5
RATE_LIMIT_WINDOW = 300  # 5 minutes
ACCOUNT_LOCKOUT_ATTEMPTS = 10  # Lock account after 10 failed attempts
ACCOUNT_LOCKOUT_DURATION = 1800  # 30 minutes
login_attempts = {}

# Enhanced Forms
class RegistrationForm(FlaskForm):
    username = StringField(
        'Username', 
        validators=[
            DataRequired(message="Username is required"),
            Length(min=3, max=50, message="Username must be between 3 and 50 characters"),
            Regexp(r'^[a-zA-Z0-9_.-]+$', message="Username can only contain letters, numbers, dots, hyphens, and underscores")
        ]
    )
    email = StringField(
        'Email', 
        validators=[
            DataRequired(message="Email is required"),
            Email(message="Please enter a valid email address"),
            Length(max=120, message="Email must be less than 120 characters")
        ]
    )
    password = PasswordField(
        'Password', 
        validators=[
            DataRequired(message="Password is required"),
            Length(min=8, max=128, message="Password must be between 8 and 128 characters")
        ]
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message="Please confirm your password"),
            EqualTo('password', message="Passwords must match")
        ]
    )
    terms_accepted = BooleanField(
        'I accept the Terms of Service and Privacy Policy',
        validators=[DataRequired(message="You must accept the terms to register")]
    )
    submit = SubmitField('Create Account')

class LoginForm(FlaskForm):
    username = StringField(
        'Username', 
        validators=[
            DataRequired(message="Username is required"),
            Length(min=3, max=50, message="Username must be between 3 and 50 characters"),
            Regexp(r'^[a-zA-Z0-9_.-]+$', message="Username can only contain letters, numbers, dots, hyphens, and underscores")
        ]
    )
    password = PasswordField(
        'Password', 
        validators=[
            DataRequired(message="Password is required"),
            Length(min=8, message="Password must be at least 8 characters")
        ]
    )
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

class ForgotPasswordForm(FlaskForm):
    email = StringField(
        'Email', 
        validators=[
            DataRequired(message="Email is required"),
            Email(message="Please enter a valid email address")
        ]
    )
    submit = SubmitField('Send Reset Link')

class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        'New Password', 
        validators=[
            DataRequired(message="Password is required"),
            Length(min=8, max=128, message="Password must be between 8 and 128 characters")
        ]
    )
    confirm_password = PasswordField(
        'Confirm New Password',
        validators=[
            DataRequired(message="Please confirm your password"),
            EqualTo('password', message="Passwords must match")
        ]
    )
    submit = SubmitField('Reset Password')

# Helper functions
def get_client_ip():
    """Get the real client IP address"""
    forwarded_ips = request.headers.get('X-Forwarded-For')
    if forwarded_ips:
        return forwarded_ips.split(',')[0].strip()
    
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip.strip()
    
    return request.remote_addr

def log_security_event(user_id, event_type, details="", ip_address=None):
    """Log security events to database and file"""
    try:
        ip_addr = ip_address or get_client_ip()
        user_agent = request.headers.get('User-Agent', '')[:500]
        
        db.execute('''
            INSERT INTO security_logs (user_id, event_type, ip_address, user_agent, details)
            VALUES (?, ?, ?, ?, ?)
        ''', user_id, event_type, ip_addr, user_agent, details)
        
        logger.info(f"Security Event: {event_type} - User: {user_id} - IP: {ip_addr} - Details: {details}")
        
    except Exception as e:
        logger.error(f"Failed to log security event: {str(e)}")

def send_email(to_email, subject, template_name, **template_vars):
    """Send email using configured SMTP server"""
    try:
        if not all([app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'], app.config['MAIL_SERVER']]):
            logger.error("Email configuration incomplete")
            return False
        
        # Render email template
        html_body = render_template(f'emails/{template_name}.html', **template_vars)
        text_body = render_template(f'emails/{template_name}.txt', **template_vars)
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = app.config['MAIL_DEFAULT_SENDER']
        msg['To'] = to_email
        
        # Attach parts
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email
        with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT']) as server:
            if app.config['MAIL_USE_TLS']:
                server.starttls()
            server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            server.send_message(msg)
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False

def generate_token():
    """Generate a secure random token"""
    return secrets.token_urlsafe(32)

def validate_password_strength(password):
    """Validate password strength"""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    if len(password) > 128:
        errors.append("Password must be less than 128 characters long")
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    if not re.search(r'[0-9]', password):
        errors.append("Password must contain at least one number")
    if not re.search(r'[^A-Za-z0-9]', password):
        errors.append("Password must contain at least one special character")
    if re.search(r'\s', password):
        errors.append("Password cannot contain spaces")
    
    return errors

def is_account_locked(username):
    """Check if account is locked due to failed login attempts"""
    try:
        user = db.execute('SELECT locked_until FROM users WHERE username = ?', username)
        if user and user[0]['locked_until']:
            locked_until = datetime.fromisoformat(user[0]['locked_until'])
            if datetime.now() < locked_until:
                return True
            else:
                db.execute('UPDATE users SET locked_until = NULL, failed_login_attempts = 0 WHERE username = ?', username)
        return False
    except Exception as e:
        logger.error(f"Error checking account lock status: {str(e)}")
        return False

def record_failed_login(username):
    """Record failed login attempt and lock account if necessary"""
    try:
        db.execute('UPDATE users SET failed_login_attempts = failed_login_attempts + 1 WHERE username = ?', username)
        
        user = db.execute('SELECT failed_login_attempts FROM users WHERE username = ?', username)
        if user and user[0]['failed_login_attempts'] >= ACCOUNT_LOCKOUT_ATTEMPTS:
            locked_until = datetime.now() + timedelta(seconds=ACCOUNT_LOCKOUT_DURATION)
            db.execute('UPDATE users SET locked_until = ? WHERE username = ?', 
                      locked_until.isoformat(), username)
            log_security_event(None, 'ACCOUNT_LOCKED', f'Account {username} locked due to failed login attempts')
            
    except Exception as e:
        logger.error(f"Error recording failed login: {str(e)}")

def check_rate_limit(ip_address, username=None):
    """Enhanced rate limiting with better error handling"""
    current_time = time.time()
    
    # Clean old entries for IP
    if ip_address in login_attempts:
        login_attempts[ip_address] = [
            t for t in login_attempts[ip_address] 
            if current_time - t < RATE_LIMIT_WINDOW
        ]
    
    # Clean old entries for username
    if username and username in login_attempts:
        login_attempts[username] = [
            t for t in login_attempts[username] 
            if current_time - t < RATE_LIMIT_WINDOW
        ]
    
    # Check rate limits
    if ip_address in login_attempts and len(login_attempts[ip_address]) >= RATE_LIMIT_ATTEMPTS:
        log_security_event(None, 'RATE_LIMIT_EXCEEDED', f'IP: {ip_address}')
        raise Exception(f"Too many login attempts from this IP. Please try again in {RATE_LIMIT_WINDOW // 60} minutes.")
    
    if username and username in login_attempts and len(login_attempts[username]) >= RATE_LIMIT_ATTEMPTS:
        log_security_event(None, 'RATE_LIMIT_EXCEEDED', f'Username: {username}')
        raise Exception(f"Too many login attempts for this user. Please try again in {RATE_LIMIT_WINDOW // 60} minutes.")

def record_login_attempt(ip_address, username=None):
    """Record login attempt for rate limiting"""
    current_time = time.time()
    
    if ip_address not in login_attempts:
        login_attempts[ip_address] = []
    login_attempts[ip_address].append(current_time)
    
    if username:
        if username not in login_attempts:
            login_attempts[username] = []
        login_attempts[username].append(current_time)



def validate_session():
    """Validate current session for security"""
    if 'user_id' not in session:
        return False
    
    # Check session timeout
    if 'login_time' in session:
        try:
            login_time = datetime.fromisoformat(session['login_time'])
            if datetime.now() - login_time > app.config['PERMANENT_SESSION_LIFETIME']:
                log_security_event(session.get('user_id'), 'SESSION_EXPIRED', 'Session timeout')
                session.clear()
                return False
        except (ValueError, TypeError):
            session.clear()
            return False
    
    return True

def is_safe_url(target):

    """Check if a redirect URL is safe to prevent open redirect attacks"""
    from urllib.parse import urlparse, urljoin
    
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)
# Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration with email verification"""
    if not app.config['REGISTRATION_ENABLED']:
        flash('Registration is currently disabled.', 'info')
        return redirect(url_for('login'))
    
    if 'user_id' in session and validate_session():
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        try:
            client_ip = get_client_ip()
            username = form.username.data.strip()
            email = form.email.data.strip().lower()
            password = form.password.data
            
            # Check rate limiting
            check_rate_limit(client_ip, username)
            record_login_attempt(client_ip, username)
            
            # Validate password strength
            password_errors = auth_service.validate_password(password)
            if password_errors:
                for error in password_errors:
                    flash(error, 'error')
                return render_template('register.html', form=form)
            
            # Check if username or email already exists
            existing_user = db.execute('''
                SELECT id FROM users WHERE username = ? OR email = ?
            ''', username, email)
            
            if existing_user:
                log_security_event(None, 'REGISTRATION_ATTEMPT_DUPLICATE', 
                                 f'Username: {username}, Email: {email}')
                flash('Username or email already exists.', 'error')
                return render_template('register.html', form=form)
            
            # Generate verification token
            verification_token = generate_token()
            verification_expires = datetime.now() + timedelta(hours=24)
            
            # Create user account (unverified)
            password_hash = generate_password_hash(password)
            user_id = db.execute('''
                INSERT INTO users (username, email, password_hash, email_verification_token, email_verification_expires)
                VALUES (?, ?, ?, ?, ?)
            ''', username, email, password_hash, verification_token, verification_expires.isoformat())
            
            # Send verification email
            verification_url = url_for('verify_email', token=verification_token, _external=True)
            email_sent = send_email(
                email,
                'Verify Your FinTrack Account',
                'email_verification',
                username=username,
                verification_url=verification_url,
                expiry_hours=24
            )
            
            if email_sent:
                log_security_event(user_id, 'REGISTRATION_SUCCESS', f'Username: {username}, Email: {email}')
                flash('Registration successful! Please check your email to verify your account.', 'success')
                return redirect(url_for('login'))
            else:
                # If email fails, delete the user account
                db.execute('DELETE FROM users WHERE id = ?', user_id)
                flash('Registration failed. Please try again later.', 'error')
                
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            flash('Registration failed. Please try again later.', 'error')
    
    return render_template('register.html', form=form)

@app.route('/verify-email/<token>')
def verify_email(token):
    """Verify email address"""
    try:
        user = db.execute('''
            SELECT * FROM users 
            WHERE email_verification_token = ? AND email_verification_expires > ?
        ''', token, datetime.now().isoformat())
        
        if not user:
            flash('Invalid or expired verification link.', 'error')
            return redirect(url_for('login'))
        
        user = user[0]
        
        # Verify the email
        db.execute('''
            UPDATE users 
            SET email_verified = TRUE, email_verification_token = NULL, email_verification_expires = NULL
            WHERE id = ?
        ''', user['id'])
        
        log_security_event(user['id'], 'EMAIL_VERIFIED', f'Email: {user["email"]}')
        flash('Email verified successfully! You can now log in.', 'success')
        
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        flash('Email verification failed. Please try again.', 'error')
    
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Initiate password reset"""
    if not app.config['PASSWORD_RESET_ENABLED']:
        flash('Password reset is currently disabled.', 'info')
        return redirect(url_for('login'))
    
    if 'user_id' in session and validate_session():
        return redirect(url_for('dashboard'))
    
    form = ForgotPasswordForm()
    
    if form.validate_on_submit():
        try:
            client_ip = get_client_ip()
            email = form.email.data.strip().lower()
            
            # Check if user exists
            user = db.execute('SELECT * FROM users WHERE email = ?', email)
            
            if user:
                user = user[0]
                
                # Generate reset token
                reset_token = generate_token()
                reset_expires = datetime.now() + timedelta(minutes=app.config['PASSWORD_RESET_TIMEOUT'])
                
                # Save reset token
                db.execute('''
                    UPDATE users 
                    SET password_reset_token = ?, password_reset_expires = ?
                    WHERE id = ?
                ''', reset_token, reset_expires.isoformat(), user['id'])
                
                # Send reset email
                reset_url = url_for('reset_password', token=reset_token, _external=True)
                email_sent = send_email(
                    email,
                    'Reset Your FinTrack Password',
                    'password_reset',
                    username=user['username'],
                    reset_url=reset_url,
                    expiry_minutes=app.config['PASSWORD_RESET_TIMEOUT']
                )
                
                if email_sent:
                    log_security_event(user['id'], 'PASSWORD_RESET_REQUESTED', f'Email: {email}')
            
            # Always show success message to prevent email enumeration
            flash('If an account with that email exists, a password reset link has been sent.', 'info')
            
        except Exception as e:
            flash(str(e), 'error')
    
    return render_template('forgot_password.html', form=form)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    try:
        user = db.execute('''
            SELECT * FROM users 
            WHERE password_reset_token = ? AND password_reset_expires > ?
        ''', token, datetime.now().isoformat())
        
        if not user:
            flash('Invalid or expired reset link.', 'error')
            return redirect(url_for('forgot_password'))
        
        user = user[0]
        form = ResetPasswordForm()
        
        if form.validate_on_submit():
            password = form.password.data
            
            # Validate password strength
            password_errors = auth_service.validate_password(password)
            if password_errors:
                for error in password_errors:
                    flash(error, 'error')
                return render_template('reset_password.html', form=form, token=token)
            
            # Update password
            password_hash = generate_password_hash(password)
            db.execute('''
                UPDATE users 
                SET password_hash = ?, password_reset_token = NULL, password_reset_expires = NULL,
                    failed_login_attempts = 0, locked_until = NULL, updated_at = ?
                WHERE id = ?
            ''', password_hash, datetime.now().isoformat(), user['id'])
            
            log_security_event(user['id'], 'PASSWORD_RESET_COMPLETED', f'User: {user["username"]}')
            flash('Password reset successfully! You can now log in with your new password.', 'success')
            return redirect(url_for('login'))
        
        return render_template('reset_password.html', form=form, token=token)
        
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        flash('Password reset failed. Please try again.', 'error')
        return redirect(url_for('forgot_password'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if 'user_id' in session and validate_session():
        return redirect(url_for('dashboard'))
    
    if form.validate_on_submit():
        try:
            client_ip = get_client_ip()
            username = form.username.data.strip()
            password = form.password.data
            remember_me = form.remember_me.data
            
            # Remove local rate limiting, let AuthService handle it
            
            # Use AuthService for authentication
            success, error = auth_service.login(username, password)
            
            if success:
                user = user_service.get_user_by_username(username)
                if not user or not user[0].get('email_verified', False):
                    log_security_event(user[0]['id'] if user else None, 'LOGIN_ATTEMPT_UNVERIFIED_EMAIL', username)
                    flash('Please verify your email address before logging in.', 'warning')
                    return render_template('login.html', form=form)
                
                # Set up session
                session.clear()
                session['user_id'] = user[0]['id']
                session['username'] = username
                session['login_time'] = datetime.now().isoformat()
                session['ip_address'] = client_ip
                session.permanent = remember_me
                
                flash('Login successful!', 'success')
                next_page = request.args.get('next')
                if next_page and is_safe_url(next_page):
                    return redirect(next_page)
                return redirect(url_for('dashboard'))
            else:
                flash(error or 'Invalid username or password.', 'error')
                
        except Exception as e:
            flash(str(e), 'error')
    
    return render_template('login.html', form=form)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """Enhanced logout function with security logging"""
    try:
        user_id = session.get('user_id')
        username = session.get('username', 'Unknown')
        client_ip = get_client_ip()
        
        # Log logout event
        log_security_event(user_id, 'LOGOUT', f'User {username} logged out from IP {client_ip}')
        
        # Clear session completely
        session.clear()
        
        flash('You have been successfully logged out.', 'info')
        return redirect(url_for('login'))
        
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        # Even if there's an error, clear the session for security
        session.clear()
        flash('Logout completed.', 'info')
        return redirect(url_for('login'))

@app.route("/dashboard")
@login_required
def dashboard():
    """Dashboard with session validation"""
    if not validate_session():
        flash('Your session has expired. Please log in again.', 'info')
        return redirect(url_for('login'))
    
    try:
        user_id = session.get('user_id')
        user = db.execute("SELECT * FROM users WHERE id = ?", user_id)
        
        if not user:
            session.clear()
            flash('User account not found. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        balance = user[0]["cash"]
        transactions = db.execute(
            "SELECT t.*, c.name as category_name FROM transactions t "
            "LEFT JOIN categories c ON t.category_id = c.id "
            "WHERE t.user_id = ? ORDER BY t.date DESC LIMIT 5", 
            user_id
        )
        
        return render_template("dashboard.html", balance=balance, transactions=transactions, user=user[0])
        
    except Exception as e:
        logger.error(f"Dashboard error for user {session.get('user_id')}: {str(e)}")
        flash('An error occurred loading the dashboard.', 'error')
        return redirect(url_for('login'))

# Other routes remain the same but should include session validation

@app.route("/transactions", methods=["GET"])
@login_required
def transactions():
    """Display all transactions for the user with secure filtering"""
    if not validate_session():
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    
    # Validate and sanitize filter parameters
    try:
        # Category filter with validation
        category_filter = request.args.get('category', type=int)
        if category_filter and category_filter <= 0:
            category_filter = None
            
        # Date validation
        date_from = request.args.get('from', '').strip()
        date_to = request.args.get('to', '').strip()
        
        # Validate date format if provided
        if date_from:
            datetime.strptime(date_from, '%Y-%m-%d')
        if date_to:
            datetime.strptime(date_to, '%Y-%m-%d')
            
        # Search with length limit and sanitization
        search = request.args.get('search', '').strip()[:100]
        
        # Escape special LIKE characters
        if search:
            search = search.replace('\\', '\\\\')
            search = search.replace('%', '\\%')
            search = search.replace('_', '\\_')
            
    except ValueError as e:
        flash('Invalid filter parameters.', 'warning')
        return redirect(url_for('transactions'))
    
    # Build query with parameterized values
    query = """
        SELECT t.*, c.name as category_name, c.type as category_type 
        FROM transactions t 
        LEFT JOIN categories c ON t.category_id = c.id 
        WHERE t.user_id = ?
    """
    params = [user_id]
    
    if category_filter:
        query += " AND t.category_id = ?"
        params.append(category_filter)
    
    if date_from:
        query += " AND DATE(t.date) >= ?"
        params.append(date_from)
    
    if date_to:
        query += " AND DATE(t.date) <= ?"
        params.append(date_to)
    
    if search:
        query += " AND t.description LIKE ? ESCAPE '\\'"
        params.append(f'%{search}%')
    
    query += " ORDER BY t.date DESC, t.id DESC LIMIT 1000"  # Limit results
    
    try:
        transactions = db.execute(query, *params)
    except Exception as e:
        logger.error(f"Error fetching transactions: {str(e)}")
        flash('Failed to load transactions.', 'error')
        transactions = []
    
    # Get categories for filter dropdown
    categories = db.execute("SELECT * FROM categories ORDER BY type, name")
    
    # Calculate totals safely
    total_income = sum(Decimal(str(t['amount'])) for t in transactions 
                      if t.get('category_type') == 'income')
    total_expense = sum(abs(Decimal(str(t['amount']))) for t in transactions 
                       if t.get('category_type') == 'expense')
    
    return render_template("transactions.html", 
                         transactions=transactions,
                         categories=categories,
                         total_income=float(total_income),
                         total_expense=float(total_expense),
                         filters={
                             'category': category_filter,
                             'date_from': date_from,
                             'date_to': date_to,
                             'search': search.replace('\\\\', '\\').replace('\\%', '%').replace('\\_', '_')
                         })

@app.route("/transactions/add", methods=["POST"])
@login_required
def add_transaction():
    """Add a new transaction with comprehensive validation"""
    if not validate_session():
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    
    # Validate amount
    amount_str = request.form.get('amount', '').strip()
    if not amount_str:
        flash('Amount is required.', 'error')
        return redirect(url_for('transactions'))
    
    try:
        amount = Decimal(amount_str)
        
        # Validate reasonable amount (prevent overflow)
        if amount <= 0:
            flash('Amount must be positive.', 'error')
            return redirect(url_for('transactions'))
        
        if amount > Decimal('999999999.99'):
            flash('Amount is too large.', 'error')
            return redirect(url_for('transactions'))
            
    except (InvalidOperation, ValueError):
        flash('Invalid amount format. Please enter a valid number.', 'error')
        return redirect(url_for('transactions'))
    
    # Validate category
    category_id = request.form.get('category_id', type=int)
    if not category_id or category_id <= 0:
        flash('Please select a valid category.', 'error')
        return redirect(url_for('transactions'))
    
    # Validate description
    description = request.form.get('description', '').strip()[:500]  # Limit length
    
    # Validate date
    date_str = request.form.get('date', '').strip()
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    else:
        try:
            # Validate date format and range
            transaction_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            # Don't allow future dates too far ahead
            if transaction_date > datetime.now() + timedelta(days=30):
                flash('Transaction date cannot be more than 30 days in the future.', 'error')
                return redirect(url_for('transactions'))
                
            # Don't allow dates too far in the past
            if transaction_date < datetime.now() - timedelta(days=365*5):
                flash('Transaction date cannot be more than 5 years in the past.', 'error')
                return redirect(url_for('transactions'))
                
        except ValueError:
            flash('Invalid date format.', 'error')
            return redirect(url_for('transactions'))
    
    try:
        # Verify category exists and belongs to valid types
        category = db.execute("""
            SELECT type FROM categories 
            WHERE id = ? AND type IN ('income', 'expense')
        """, category_id)
        
        if not category:
            flash('Invalid category selected.', 'error')
            return redirect(url_for('transactions'))
        
        # Adjust amount sign based on category type
        if category[0]['type'] == 'expense':
            amount = -abs(amount)
        else:
            amount = abs(amount)
        
        # Begin transaction for atomicity
        # Insert transaction
        transaction_id = db.execute("""
            INSERT INTO transactions (user_id, category_id, amount, description, date, currency)
            VALUES (?, ?, ?, ?, ?, ?)
        """, user_id, category_id, float(amount), description, date_str, 'USD')
        
        # Update user's cash balance
        db.execute("""
            UPDATE users 
            SET cash = cash + ?, updated_at = ? 
            WHERE id = ?
        """, float(amount), datetime.now().isoformat(), user_id)
        
        flash('Transaction added successfully!', 'success')
        log_security_event(user_id, 'TRANSACTION_ADDED', 
                         f'ID: {transaction_id}, Amount: {amount}, Category: {category_id}')
        
    except Exception as e:
        logger.error(f"Error adding transaction for user {user_id}: {str(e)}")
        flash('Failed to add transaction. Please try again.', 'error')
    
    return redirect(url_for('transactions'))

@app.route("/transactions/<int:transaction_id>/edit", methods=["GET", "POST"])
@login_required
def edit_transaction(transaction_id):
    """Edit an existing transaction"""
    if not validate_session():
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    
    # Verify transaction belongs to user
    transactions = db.execute("""
        SELECT t.*, c.type as category_type 
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        WHERE t.id = ? AND t.user_id = ?
    """, transaction_id, user_id)
    
    if not transactions:
        flash('Transaction not found.', 'error')
        return redirect(url_for('transactions'))
    
    transactions = transactions[0]
    
    if request.method == "POST":
        # Similar validation as add_transaction
        amount_str = request.form.get('amount', '').strip()
        if not amount_str:
            flash('Amount is required.', 'error')
            return redirect(url_for('edit_transaction', transaction_id=transaction_id))
        
        try:
            new_amount = Decimal(amount_str)
            if new_amount <= 0 or new_amount > Decimal('999999999.99'):
                flash('Invalid amount.', 'error')
                return redirect(url_for('edit_transaction', transaction_id=transaction_id))
        except (InvalidOperation, ValueError):
            flash('Invalid amount format.', 'error')
            return redirect(url_for('edit_transaction', transaction_id=transaction_id))
        
        category_id = request.form.get('category_id', type=int)
        description = request.form.get('description', '').strip()[:500]
        date_str = request.form.get('date', '').strip()
        
        try:
            # Get new category type
            category = db.execute("SELECT type FROM categories WHERE id = ?", category_id)
            if not category:
                flash('Invalid category.', 'error')
                return redirect(url_for('edit_transaction', transaction_id=transaction_id))
            
            # Adjust amount sign
            if category[0]['type'] == 'expense':
                new_amount = -abs(new_amount)
            else:
                new_amount = abs(new_amount)
            
            # Calculate balance adjustment
            old_amount = Decimal(str(transactions['amount']))
            balance_adjustment = new_amount - old_amount
            
            # Update transaction
            db.execute("""
                UPDATE transactions 
                SET category_id = ?, amount = ?, description = ?, date = ?
                WHERE id = ? AND user_id = ?
            """, category_id, float(new_amount), description, date_str, 
                transaction_id, user_id)
            
            # Update user balance
            db.execute("""
                UPDATE users 
                SET cash = cash + ?, updated_at = ?
                WHERE id = ?
            """, float(balance_adjustment), datetime.now().isoformat(), user_id)
            
            flash('Transaction updated successfully!', 'success')
            log_security_event(user_id, 'TRANSACTION_EDITED', f'ID: {transaction_id}')
            return redirect(url_for('transactions'))
            
        except Exception as e:
            logger.error(f"Error editing transaction: {str(e)}")
            flash('Failed to update transaction.', 'error')
    
    # GET request - show edit form
    categories = db.execute("SELECT * FROM categories ORDER BY type, name")
    return render_template("edit_transactions.html", 
                         transactions=transactions, 
                         categories=categories)

@app.route("/transactions/<int:transaction_id>/delete", methods=["POST"])
@login_required
def delete_transaction(transaction_id):
    """Delete a transaction with proper validation and atomicity"""
    if not validate_session():
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    
    try:
        # Verify transaction belongs to user and get amount
        transaction = db.execute("""
            SELECT id, amount FROM transactions 
            WHERE id = ? AND user_id = ?
        """, transaction_id, user_id)
        
        if not transaction:
            flash('Transaction not found or access denied.', 'error')
            return redirect(url_for('transactions'))
        
        amount = Decimal(str(transaction[0]['amount']))
        
        # Delete transaction
        db.execute("""
            DELETE FROM transactions 
            WHERE id = ? AND user_id = ?
        """, transaction_id, user_id)
        
        # Reverse the balance change
        db.execute("""
            UPDATE users 
            SET cash = cash - ?, updated_at = ?
            WHERE id = ?
        """, float(amount), datetime.now().isoformat(), user_id)
        
        flash('Transaction deleted successfully!', 'success')
        log_security_event(user_id, 'TRANSACTION_DELETED', 
                         f'ID: {transaction_id}, Amount: {amount}')
        
    except Exception as e:
        logger.error(f"Error deleting transaction {transaction_id}: {str(e)}")
        flash('Failed to delete transaction. Please try again.', 'error')
    
    return redirect(url_for('transactions'))

@app.route("/budget", methods=["GET", "POST"])
@login_required
def budget():
    if not validate_session():
        return redirect(url_for('login'))
    return render_template("budget.html")

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if not validate_session():
        return redirect(url_for('login'))
    return render_template("profile.html")

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return render_template('500.html'), 500

@app.errorhandler(429)
def rate_limit_error(error):
    return render_template('rate_limit.html'), 429

@app.after_request
def security_headers(response):
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

if __name__ == '__main__':
    """Run the Flask application with enhanced security features"""
    # Initialiser la base de données au démarrage
    init_db()

    # Production security checks
    if os.environ.get('FLASK_ENV') == 'production':
        required_env_vars = [
            'SECRET_KEY',
            'MAIL_USERNAME',
            'MAIL_PASSWORD',
            'MAIL_DEFAULT_SENDER'
        ]
        
        missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            exit(1)
        
        logger.info("Starting FinTrack in production mode")
        app.run(
            host="0.0.0.0",
            port=int(os.environ.get('PORT', 5000)),
            debug=False,
            ssl_context='adhoc' if os.environ.get('USE_SSL') == 'true' else None
        )
    else:
        logger.warning("Running in development mode")
        app.run(
            debug=True,
            host="127.0.0.1",
            port=5000
        )