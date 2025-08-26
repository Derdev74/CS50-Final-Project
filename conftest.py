"""
Test configuration and fixtures for FinTrack application.

This module provides pytest fixtures for setting up test databases,
authenticated clients, and test data. All fixtures ensure proper
database coordination and test isolation.

Security considerations:
- Uses separate test database to prevent data corruption
- Proper database connection sharing between fixtures
- Creates isolated test users for each test
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from app import app
from cs50 import SQL

@pytest.fixture(scope="function")
def test_db():
    """
    Create and configure test database with proper connection sharing.
    
    This fixture creates a temporary database file and ensures all
    fixtures use the same database connection for consistency.
    
    Security: Uses temporary file that's automatically cleaned up
    """
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    # Create database connection
    test_db_instance = SQL(f"sqlite:///{db_path}")
    
    # Initialize database schema directly with this connection
    _initialize_test_database(test_db_instance)
    
    yield test_db_instance
    
    # Cleanup: Close and remove temporary database
    os.close(db_fd)
    os.unlink(db_path)

def _initialize_test_database(db):
    """
    Initialize test database with complete schema.
    
    This function replicates the init_db() functionality but uses
    the provided database connection to ensure consistency.
    
    Args:
        db: Database connection instance
    """
    # Users table - core user account information
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
            preferred_currency TEXT DEFAULT 'USD',
            failed_login_attempts INTEGER DEFAULT 0,
            locked_until TIMESTAMP NULL,
            last_login TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Categories table - transaction categories
    db.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT CHECK(type IN ('income', 'expense')) NOT NULL
        )
    ''')
    
    # User-defined categories table
    db.execute('''
        CREATE TABLE IF NOT EXISTS user_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            type TEXT CHECK(type IN ('income', 'expense')) NOT NULL,
            icon TEXT,
            color TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, name)
        )
    ''')
    
    # Transactions table - financial transactions
    db.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER,
            amount NUMERIC NOT NULL,
            original_amount NUMERIC,
            currency TEXT DEFAULT 'USD',
            exchange_rate NUMERIC DEFAULT 1.0,
            description TEXT,
            date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
        )
    ''')
    
    # Budgets table - spending budgets
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
    
    # Goals table - savings goals
    db.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            target_amount NUMERIC NOT NULL,
            current_amount NUMERIC DEFAULT 0,
            deadline DATE,
            goal_type TEXT DEFAULT 'savings',
            notes TEXT,
            color TEXT DEFAULT '#4CAF50',
            is_recurring BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
    
    # Currency exchange rates cache table
    db.execute('''
        CREATE TABLE IF NOT EXISTS exchange_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            base_currency TEXT NOT NULL DEFAULT 'USD',
            target_currency TEXT NOT NULL,
            rate NUMERIC NOT NULL,
            last_updated TIMESTAMP NOT NULL,
            UNIQUE(base_currency, target_currency)
        )
    ''')
    
    # Insert default categories
    default_categories = [
        ('Food & Dining', 'expense'),
        ('Transportation', 'expense'),
        ('Shopping', 'expense'),
        ('Entertainment', 'expense'),
        ('Bills & Utilities', 'expense'),
        ('Healthcare', 'expense'),
        ('Education', 'expense'),
        ('Personal Care', 'expense'),
        ('Gifts & Donations', 'expense'),
        ('Salary', 'income'),
        ('Freelance', 'income'),
        ('Investments', 'income'),
        ('Business', 'income'),
        ('Other Income', 'income'),
        ('Other Expense', 'expense')
    ]
    
    for name, cat_type in default_categories:
        db.execute('INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)', name, cat_type)

@pytest.fixture
def app_context(test_db):
    """
    Create application context for testing with proper database.
    
    This fixture ensures Flask's application context is available
    during tests and configures the app to use the test database.
    """
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    app.config['DATABASE_PATH'] = ':memory:'  # Override for testing
    
    with app.app_context():
        # Monkey patch the global db instance to use our test database
        import app as app_module
        original_db = app_module.db
        app_module.db = test_db
        
        yield app
        
        # Restore original db
        app_module.db = original_db

@pytest.fixture
def client(app_context):
    """
    Create a test client for making HTTP requests.
    
    This fixture provides a Flask test client that uses the test database
    and maintains session state across requests within a test.
    """
    with app.test_client() as client:
        yield client

@pytest.fixture
def test_user(test_db):
    """
    Create a test user in the database.
    
    Creates a verified user account for testing authenticated functionality.
    The user has a known password and verified email status.
    
    Returns:
        dict: User information including ID, username, and password
    """
    password = "TestPassword123!"
    password_hash = generate_password_hash(password)
    
    user_id = test_db.execute("""
        INSERT INTO users (
            username, email, password_hash, email_verified,
            cash, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, 
    'testuser', 'test@example.com', password_hash, True,
    10000.00, datetime.now().isoformat(), datetime.now().isoformat())
    
    return {
        'id': user_id,
        'username': 'testuser',
        'email': 'test@example.com',
        'password': password,  # Plain text for testing login
        'cash': 10000.00
    }

@pytest.fixture
def authenticated_client(client, test_user):
    """
    Create an authenticated test client.
    
    This fixture provides a test client that's already logged in
    as the test user, allowing tests of protected routes without
    needing to handle authentication in each test.
    
    Security: Uses proper login flow rather than bypassing authentication
    """
    # Perform login through the normal login route
    response = client.post('/login', data={
        'username': test_user['username'],
        'password': test_user['password']
    })
    
    # Verify login was successful (should redirect or return success)
    assert response.status_code in [200, 302]
    
    yield client

@pytest.fixture
def test_categories(test_db):
    """
    Get default categories from database.
    
    Returns the default categories that are created during database
    initialization for testing transaction creation and budget management.
    
    Returns:
        list: Category records with id, name, and type
    """
    categories = test_db.execute("""
        SELECT id, name, type 
        FROM categories 
        ORDER BY type, name
    """)
    
    # Ensure we have both income and expense categories
    income_cats = [c for c in categories if c['type'] == 'income']
    expense_cats = [c for c in categories if c['type'] == 'expense']
    
    assert len(income_cats) > 0, "No income categories found"
    assert len(expense_cats) > 0, "No expense categories found"
    
    return categories

@pytest.fixture
def test_transactions(test_db, test_user, test_categories):
    """
    Create test transactions for testing.
    
    Creates a variety of test transactions (income and expense)
    across different categories and dates for comprehensive testing.
    
    Returns:
        list: Transaction records
    """
    transactions = []
    
    # Create income transaction
    income_cat = next(c for c in test_categories if c['type'] == 'income')
    txn_id = test_db.execute("""
        INSERT INTO transactions (
            user_id, category_id, amount, description, date, currency
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, test_user['id'], income_cat['id'], 500.00, 
        'Test Income', datetime.now().isoformat(), 'USD')
    
    transactions.append({
        'id': txn_id,
        'amount': 500.00,
        'category_id': income_cat['id'],
        'type': 'income'
    })
    
    # Create expense transaction
    expense_cat = next(c for c in test_categories if c['type'] == 'expense')
    txn_id = test_db.execute("""
        INSERT INTO transactions (
            user_id, category_id, amount, description, date, currency
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, test_user['id'], expense_cat['id'], -200.00,
        'Test Expense', datetime.now().isoformat(), 'USD')
    
    transactions.append({
        'id': txn_id,
        'amount': -200.00,
        'category_id': expense_cat['id'],
        'type': 'expense'
    })
    
    return transactions

@pytest.fixture
def test_budget(test_db, test_user, test_categories):
    """
    Create a test budget.
    
    Creates a monthly expense budget for testing budget functionality.
    
    Returns:
        dict: Budget record
    """
    expense_cat = next(c for c in test_categories if c['type'] == 'expense')
    
    budget_id = test_db.execute("""
        INSERT INTO budgets (
            user_id, category_id, amount, period, start_date
        ) VALUES (?, ?, ?, ?, ?)
    """, test_user['id'], expense_cat['id'], 1000.00, 
        'monthly', datetime.now().strftime('%Y-%m-%d'))
    
    return {
        'id': budget_id,
        'category_id': expense_cat['id'],
        'amount': 1000.00,
        'period': 'monthly'
    }

@pytest.fixture
def test_goal(test_db, test_user):
    """
    Create a test savings goal.
    
    Creates a savings goal with partial progress for testing
    goal management functionality.
    
    Returns:
        dict: Goal record
    """
    deadline = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
    
    goal_id = test_db.execute("""
        INSERT INTO goals (
            user_id, name, target_amount, current_amount, deadline
        ) VALUES (?, ?, ?, ?, ?)
    """, test_user['id'], 'Test Vacation Fund', 5000.00, 1000.00, deadline)
    
    return {
        'id': goal_id,
        'name': 'Test Vacation Fund',
        'target_amount': 5000.00,
        'current_amount': 1000.00,
        'deadline': deadline
    }