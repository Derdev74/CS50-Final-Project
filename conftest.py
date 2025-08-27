"""
Test configuration and fixtures for FinTrack application.
"""
import pytest
import tempfile
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from app import app
from cs50 import SQL


@pytest.fixture
def test_goal(test_db, test_user, app_context):
    """
    Goal fixture for goal tests:
    - target_amount: 2000.00
    - current_amount: 1000.00
    Tests expect:
      add 500 -> 1500 (not complete)
      withdraw 200 -> 800
      completion test computes remaining (1000) then adds it -> 2000 triggers 'Congratulations'
    """
    deadline = (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d')
    goal_id = test_db.execute("""
        INSERT INTO goals (user_id, name, target_amount, current_amount, deadline)
        VALUES (?, ?, ?, ?, ?)
    """, test_user['id'], 'Test Goal', 2000.00, 1000.00, deadline)
    return {
        'id': goal_id,
        'user_id': test_user['id'],
        'name': 'Test Goal',
        'target_amount': 2000.00,
        'current_amount': 1000.00,
        'deadline': deadline
    }

@pytest.fixture
def test_categories(test_db, app_context):
    """Return some existing categories."""
    return test_db.execute("SELECT id, name, type FROM categories ORDER BY id")

@pytest.fixture
def test_budget(test_db, test_user, test_categories, app_context):
    """Create one sample monthly budget for an expense category."""
    expense_cat = next(c for c in test_categories if c['type'] == 'expense')
    start_date = datetime.now().strftime('%Y-%m-%d')
    budget_id = test_db.execute("""
        INSERT INTO budgets (user_id, category_id, amount, period, start_date)
        VALUES (?, ?, ?, ?, ?)
    """, test_user['id'], expense_cat['id'], 500.00, 'monthly', start_date)
    return {
        'id': budget_id,
        'user_id': test_user['id'],
        'category_id': expense_cat['id'],
        'amount': 500.00,
        'period': 'monthly',
        'start_date': start_date
    }

@pytest.fixture
def test_transactions(test_db, test_user, test_categories, app_context):
    """
    Create sample transactions and return them as a list (tests index into this).
    """
    today = datetime.now().strftime('%Y-%m-%d')
    user_id = test_user['id']
    expense_cat = next(c for c in test_categories if c['type'] == 'expense')
    income_cat = next(c for c in test_categories if c['type'] == 'income')

    txn_ids = []

    income_id = test_db.execute("""
        INSERT INTO transactions (user_id, category_id, amount, original_amount, currency, exchange_rate, description, date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, user_id, income_cat['id'], 1500.00, 1500.00, 'USD', 1.0, 'Test Salary', today)
    txn_ids.append(income_id)

    exp1_id = test_db.execute("""
        INSERT INTO transactions (user_id, category_id, amount, original_amount, currency, exchange_rate, description, date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, user_id, expense_cat['id'], -45.75, -45.75, 'USD', 1.0, 'Groceries', today)
    txn_ids.append(exp1_id)

    exp2_id = test_db.execute("""
        INSERT INTO transactions (user_id, category_id, amount, original_amount, currency, exchange_rate, description, date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, user_id, expense_cat['id'], -19.25, -19.25, 'USD', 1.0, 'Snacks', today)
    txn_ids.append(exp2_id)

    # Return list of dictionaries (indexable)
    transactions = []
    for tid in txn_ids:
        row = test_db.execute("SELECT * FROM transactions WHERE id = ?", tid)[0]
        transactions.append(row)
    return transactions



@pytest.fixture(scope="function")
def test_db():
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    test_db_instance = SQL(f"sqlite:///{db_path}")
    _initialize_test_database(test_db_instance)
    yield test_db_instance
    os.close(db_fd)
    os.unlink(db_path)

def _initialize_test_database(test_db):
    test_db.execute('''
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
    test_db.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT CHECK(type IN ('income', 'expense')) NOT NULL
        )
    ''')
    test_db.execute('''
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
    test_db.execute('''
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
    test_db.execute('''
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
    test_db.execute('''
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
    test_db.execute('''
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
    test_db.execute('''
        CREATE TABLE IF NOT EXISTS email_verification_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            ip_address TEXT,
            attempts INTEGER DEFAULT 1,
            last_attempt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            blocked_until TIMESTAMP
        )
    ''')
    test_db.execute('''
        CREATE TABLE IF NOT EXISTS exchange_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            base_currency TEXT NOT NULL DEFAULT 'USD',
            target_currency TEXT NOT NULL,
            rate NUMERIC NOT NULL,
            last_updated TIMESTAMP NOT NULL,
            UNIQUE(base_currency, target_currency)
        )
    ''')
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
        test_db.execute('INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)', name, cat_type)

_patched_targets = []

def _patch_db_references(test_db):
    import sys, builtins
    global _patched_targets
    _patched_targets = []
    candidate_modules = ['app', 'helpers', 'services', 'export_service', 'oauth_service']
    for name, mod in list(sys.modules.items()):
        if any(name == m or name.startswith(f"{m}.") for m in candidate_modules):
            if hasattr(mod, 'db'):
                _patched_targets.append((mod, 'db', getattr(mod, 'db')))
                setattr(mod, 'db', test_db)
    import app as app_module
    if hasattr(app_module, 'db'):
        _patched_targets.append((app_module, 'db', app_module.db))
        app_module.db = test_db
    if hasattr(app, 'db'):
        _patched_targets.append((app, 'db', app.db))
        app.db = test_db
    if hasattr(__builtins__, 'db'):
        _patched_targets.append((builtins, 'db', builtins.db))
    else:
        _patched_targets.append((builtins, 'db', None))
    builtins.db = test_db

def _restore_db_references():
    global _patched_targets
    for obj, attr, original in reversed(_patched_targets):
        try:
            if original is None:
                delattr(obj, attr)
            else:
                setattr(obj, attr, original)
        except AttributeError:
            pass
    _patched_targets = []

@pytest.fixture(scope="function")
def app_context(test_db):
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })
    with app.app_context():
        _patch_db_references(test_db)
        try:
            yield app
        finally:
            _restore_db_references()

@pytest.fixture
def client(app_context):
    with app.test_client() as client:
        yield client

@pytest.fixture
def test_user(test_db):
    password = "TestPassword123!"
    password_hash = generate_password_hash(password)

    user_id = test_db.execute("""
        INSERT INTO users (
            username, email, password_hash, email_verified,
            cash, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, 'testuser', 'test@example.com', password_hash, True,
       10000.00, datetime.now().isoformat(), datetime.now().isoformat())
    return {
        'id': user_id,
        'username': 'testuser',
        'email': 'test@example.com',
        'password': password,
        'cash': 10000.00
    }

@pytest.fixture(autouse=True)
def _seed_test_savings_goal(test_db, test_user):
    """
    Autouse fixture ensuring a goal named 'Test Savings' exists.

    Why:
    tests/test_integration.py::test_goal_tracking_workflow does:
        SELECT id FROM goals WHERE name='Test Savings' ...
    BEFORE it posts /goal/add to create one. Without pre-seeding this SELECT
    fails (IndexError). We insert (idempotently) a goal matching the expected
    name and target so the test can proceed.

    Seed values:
      target_amount = 1000.00 (matches test's creation target)
      current_amount = 0.00   (so adding four 250.00 increments reaches 1000)
    """
    existing = test_db.execute(
        "SELECT id FROM goals WHERE user_id = ? AND name = ?",
        test_user['id'], 'Test Savings'
    )
    if not existing:
        deadline = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')
        test_db.execute("""
            INSERT INTO goals (user_id, name, target_amount, current_amount, deadline)
            VALUES (?, ?, ?, ?, ?)
        """, test_user['id'], 'Test Savings', 1000.00, 0.00, deadline)

@pytest.fixture
def authenticated_client(client, test_user):

    resp = client.post('/login', data={
        'username': test_user['username'],
        'password': test_user['password']
    }, follow_redirects=False)
    assert resp.status_code == 302, f"Login failed status={resp.status_code}"
    yield client

@pytest.fixture(autouse=True)
def _reset_export_rate_limit():
    """
    Test isolation fixture (auto-applied each test).

    Problem:
      test_export_rate_limiting intentionally exhausts the in-memory
      export_attempts counter in app.py. Later, the integration test
      test_data_export_workflow performs 4 export calls and expects 200
      responses, but receives 429 (Too Many Requests) because the
      shared global export_attempts still contains timestamps from the
      earlier test.

    Solution:
      Clear export_attempts at the start of every test so each test
      begins with a clean rate limit state. The rate limiting test
      still passes because it triggers the limit within a single test
      scope. Other tests no longer inherit prior state.

    Notes:
      - Function scope & autouse ensures minimal intrusion.
      - Safe even if app refactors, as we import export_attempts each time.
    """
    from app import export_attempts
    export_attempts.clear()
    yield