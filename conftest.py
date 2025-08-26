"""
Pytest configuration and fixtures for FinTrack application tests.

This module provides reusable fixtures for database setup, user authentication,
and test data generation across all test modules.
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from decimal import Decimal
from faker import Faker
from werkzeug.security import generate_password_hash

# Import your Flask app
from app import app as flask_app, db, init_db

fake = Faker()

@pytest.fixture(scope='session')
def app():
    """Create and configure a test Flask application instance."""
    # Use a temporary database for testing
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    flask_app.config.update({
        'TESTING': True,
        'DATABASE': db_path,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for testing
        'MAIL_SUPPRESS_SEND': True,  # Don't send actual emails
    })
    
    # Initialize test database
    with flask_app.app_context():
        init_db()
    
    yield flask_app
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture(scope='function')
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()

@pytest.fixture(scope='function')
def runner(app):
    """Create a test CLI runner for the Flask application."""
    return app.test_cli_runner()

@pytest.fixture(scope='function')
def authenticated_client(client, test_user):
    """Create an authenticated test client."""
    client.post('/login', data={
        'username': test_user['username'],
        'password': test_user['password']
    })
    return client

@pytest.fixture(scope='function')
def test_user(app):
    """Create a test user in the database."""
    with app.app_context():
        username = fake.user_name()
        email = fake.email()
        password = 'TestPassword123!'
        
        user_id = db.execute(
            """INSERT INTO users (username, email, password_hash, email_verified, cash)
               VALUES (?, ?, ?, ?, ?)""",
            username, email, generate_password_hash(password), True, 10000.00
        )
        
        return {
            'id': user_id,
            'username': username,
            'email': email,
            'password': password,
            'cash': 10000.00
        }

@pytest.fixture(scope='function')
def test_categories(app):
    """Create test categories."""
    with app.app_context():
        # Use unique names to avoid conflicts with default categories
        categories = [
            (f'Test Food {fake.random_int(1000, 9999)}', 'expense'),
            (f'Test Transport {fake.random_int(1000, 9999)}', 'expense'),
            (f'Test Salary {fake.random_int(1000, 9999)}', 'income'),
        ]
        
        created = []
        for name, cat_type in categories:
            cat_id = db.execute(
                "INSERT INTO categories (name, type) VALUES (?, ?)",
                name, cat_type
            )
            created.append({'id': cat_id, 'name': name, 'type': cat_type})
        
        return created

@pytest.fixture(scope='function')
def test_transactions(app, test_user, test_categories):
    """Create test transactions."""
    with app.app_context():
        transactions = []
        
        for i in range(5):
            category = test_categories[i % len(test_categories)]
            amount = fake.random_int(min=10, max=1000)
            if category['type'] == 'expense':
                amount = -amount
            
            txn_id = db.execute(
                """INSERT INTO transactions (user_id, category_id, amount, description, date)
                   VALUES (?, ?, ?, ?, ?)""",
                test_user['id'], category['id'], amount,
                fake.sentence(), datetime.now() - timedelta(days=i)
            )
            
            transactions.append({
                'id': txn_id,
                'amount': amount,
                'category_id': category['id']
            })
        
        return transactions

@pytest.fixture(scope='function')
def test_budget(app, test_user, test_categories):
    """Create a test budget."""
    with app.app_context():
        expense_category = next(c for c in test_categories if c['type'] == 'expense')
        
        budget_id = db.execute(
            """INSERT INTO budgets (user_id, category_id, amount, period, start_date)
               VALUES (?, ?, ?, ?, ?)""",
            test_user['id'], expense_category['id'], 1000.00,
            'monthly', datetime.now().date()
        )
        
        return {
            'id': budget_id,
            'category_id': expense_category['id'],
            'amount': 1000.00,
            'period': 'monthly'
        }

@pytest.fixture(scope='function')
def test_goal(app, test_user):
    """Create a test goal."""
    with app.app_context():
        goal_id = db.execute(
            """INSERT INTO goals (user_id, name, target_amount, current_amount, deadline)
               VALUES (?, ?, ?, ?, ?)""",
            test_user['id'], 'Test Vacation Fund', 5000.00, 1000.00,
            (datetime.now() + timedelta(days=365)).date()
        )
        
        return {
            'id': goal_id,
            'name': 'Test Vacation Fund',
            'target_amount': 5000.00,
            'current_amount': 1000.00
        }