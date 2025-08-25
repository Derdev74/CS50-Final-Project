"""
Pytest configuration and fixtures for FinTrack application testing.

This module provides shared fixtures and configuration for all tests,
including database setup, test client, and mock data generation.
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from decimal import Decimal
from faker import Faker
from werkzeug.security import generate_password_hash

# Import your Flask app and dependencies
from app import app, db, init_db
from services import AuthService, UserService
from helpers import CurrencyService
from export_service import ExportService

fake = Faker()

@pytest.fixture(scope='session')
def test_app():
    """Create and configure a test Flask application."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    # Configure the app for testing
    app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key-123',
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for testing
        'DATABASE': db_path,
        'REGISTRATION_ENABLED': True,
        'PASSWORD_RESET_ENABLED': True,
        'PASSWORD_RESET_TIMEOUT': 15,
        'MAIL_SERVER': 'localhost',
        'MAIL_PORT': 25,
        'MAIL_USE_TLS': False,
        'MAIL_USERNAME': 'test@example.com',
        'MAIL_PASSWORD': 'testpass',
        'MAIL_DEFAULT_SENDER': 'test@example.com',
        'PERMANENT_SESSION_LIFETIME': timedelta(hours=24)
    })
    
    # Initialize the database
    with app.app_context():
        global db
        from cs50 import SQL
        db = SQL(f"sqlite:///{db_path}")
        init_db()
    
    yield app
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(test_app):
    """Create a test client for the Flask application."""
    return test_app.test_client()

@pytest.fixture
def runner(test_app):
    """Create a test runner for CLI commands."""
    return test_app.test_cli_runner()

@pytest.fixture
def auth_service():
    """Create an AuthService instance for testing."""
    user_service = UserService(db)
    return AuthService(user_service)

@pytest.fixture
def currency_service():
    """Create a CurrencyService instance for testing."""
    return CurrencyService(db)

@pytest.fixture
def export_service():
    """Create an ExportService instance for testing."""
    return ExportService(db)

@pytest.fixture
def test_user():
    """Create a test user in the database."""
    username = fake.user_name()
    email = fake.email()
    password = 'TestPass123!'
    password_hash = generate_password_hash(password)
    
    user_id = db.execute("""
        INSERT INTO users (username, email, password_hash, email_verified, cash)
        VALUES (?, ?, ?, TRUE, 10000.00)
    """, username, email, password_hash)
    
    return {
        'id': user_id,
        'username': username,
        'email': email,
        'password': password,
        'password_hash': password_hash
    }

@pytest.fixture
def authenticated_client(client, test_user):
    """Create an authenticated test client."""
    # Login the test user
    response = client.post('/login', data={
        'username': test_user['username'],
        'password': test_user['password'],
        'remember_me': False
    }, follow_redirects=True)
    
    return client

@pytest.fixture
def test_categories():
    """Create test categories in the database."""
    categories = [
        ('Test Food', 'expense'),
        ('Test Transport', 'expense'),
        ('Test Salary', 'income'),
        ('Test Freelance', 'income')
    ]
    
    category_ids = []
    for name, cat_type in categories:
        cat_id = db.execute(
            "INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)",
            name, cat_type
        )
        if cat_id:
            category_ids.append(cat_id)
    
    return category_ids

@pytest.fixture
def test_transactions(test_user, test_categories):
    """Create test transactions for a user."""
    transactions = []
    
    for i in range(10):
        amount = fake.random_int(min=10, max=1000)
        if i % 2 == 0:
            amount = -amount  # Make some expenses
            category_id = test_categories[0]  # Expense category
        else:
            category_id = test_categories[2]  # Income category
        
        trans_id = db.execute("""
            INSERT INTO transactions (user_id, category_id, amount, description, date)
            VALUES (?, ?, ?, ?, ?)
        """, test_user['id'], category_id, amount, 
            fake.sentence(), datetime.now() - timedelta(days=i))
        
        transactions.append({
            'id': trans_id,
            'amount': amount,
            'category_id': category_id
        })
    
    return transactions

@pytest.fixture
def test_budget(test_user, test_categories):
    """Create a test budget for a user."""
    budget_id = db.execute("""
        INSERT INTO budgets (user_id, category_id, amount, period, start_date)
        VALUES (?, ?, ?, ?, ?)
    """, test_user['id'], test_categories[0], 500.00, 'monthly', 
        datetime.now().strftime('%Y-%m-%d'))
    
    return {
        'id': budget_id,
        'amount': 500.00,
        'category_id': test_categories[0]
    }

@pytest.fixture
def test_goal(test_user):
    """Create a test goal for a user."""
    goal_id = db.execute("""
        INSERT INTO goals (user_id, name, target_amount, current_amount, deadline)
        VALUES (?, ?, ?, ?, ?)
    """, test_user['id'], 'Test Vacation', 5000.00, 1000.00,
        (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d'))
    
    return {
        'id': goal_id,
        'name': 'Test Vacation',
        'target_amount': 5000.00,
        'current_amount': 1000.00
    }