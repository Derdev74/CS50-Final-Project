"""
Test suite for transaction management functionality.

Tests transaction CRUD operations, filtering, and currency conversion.
"""
from app import db
import pytest
from decimal import Decimal
from datetime import datetime, timedelta

class TestTransactions:
    """Test transaction-related functionality."""
    
    def test_view_transactions_list(self, authenticated_client, test_transactions):
        """Test viewing the transactions list."""
        response = authenticated_client.get('/transactions')
        
        assert response.status_code == 200
        assert b'Transactions' in response.data
    
    def test_add_expense_transaction(self, authenticated_client, test_user, test_categories, app):
        """Test adding an expense transaction."""
        expense_category = next(c for c in test_categories if c['type'] == 'expense')
        
        response = authenticated_client.post('/transactions/add', data={
            'amount': '50.00',
            'category_id': expense_category['id'],
            'description': 'Test expense',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'currency': 'USD'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Transaction added successfully' in response.data
        
        # Verify balance was updated
        with app.app_context():
            user = db.execute("SELECT cash FROM users WHERE id = ?", test_user['id'])
            assert user[0]['cash'] < test_user['cash']
    
    def test_add_income_transaction(self, authenticated_client, test_user, test_categories, app):
        """Test adding an income transaction."""
        income_category = next(c for c in test_categories if c['type'] == 'income')
        
        response = authenticated_client.post('/transactions/add', data={
            'amount': '100.00',
            'category_id': income_category['id'],
            'description': 'Test income',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'currency': 'USD'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Transaction added successfully' in response.data
        
        # Verify balance was updated
        with app.app_context():
            user = db.execute("SELECT cash FROM users WHERE id = ?", test_user['id'])
            assert user[0]['cash'] > test_user['cash']
    
    def test_add_transaction_invalid_amount(self, authenticated_client, test_categories):
        """Test adding transaction with invalid amount."""
        response = authenticated_client.post('/transactions/add', data={
            'amount': 'invalid',
            'category_id': test_categories[0]['id'],
            'description': 'Test',
            'date': datetime.now().strftime('%Y-%m-%d')
        })
        
        assert b'Invalid amount' in response.data
    
    def test_edit_transaction(self, authenticated_client, test_transactions, test_categories):
        """Test editing a transaction."""
        transaction = test_transactions[0]
        new_category = test_categories[1]
        
        response = authenticated_client.post(
            f'/transactions/{transaction["id"]}/edit',
            data={
                'amount': '75.00',
                'category_id': new_category['id'],
                'description': 'Updated description',
                'date': datetime.now().strftime('%Y-%m-%d')
            },
            follow_redirects=True
        )
        
        assert response.status_code == 200
        assert b'Transaction updated successfully' in response.data
    
    def test_delete_transaction(self, authenticated_client, test_transactions, app):
        """Test deleting a transaction."""
        transaction = test_transactions[0]
        
        response = authenticated_client.post(
            f'/transactions/{transaction["id"]}/delete',
            follow_redirects=True
        )
        
        assert response.status_code == 200
        assert b'Transaction deleted successfully' in response.data
        
        # Verify transaction was deleted
        with app.app_context():
            txn = db.execute("SELECT * FROM transactions WHERE id = ?", transaction['id'])
            assert len(txn) == 0
    
    def test_transaction_filtering(self, authenticated_client, test_transactions, test_categories):
        """Test transaction filtering by category and date."""
        category = test_categories[0]
        
        # Filter by category
        response = authenticated_client.get(f'/transactions?category={category["id"]}')
        assert response.status_code == 200
        
        # Filter by date range
        date_from = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        date_to = datetime.now().strftime('%Y-%m-%d')
        response = authenticated_client.get(f'/transactions?from={date_from}&to={date_to}')
        assert response.status_code == 200
    
    def test_transaction_pagination(self, authenticated_client, test_user, test_categories, app):
        """Test transaction pagination."""
        # Create 25 transactions (more than per_page limit)
        with app.app_context():
            for i in range(25):
                db.execute(
                    """INSERT INTO transactions (user_id, category_id, amount, description, date)
                       VALUES (?, ?, ?, ?, ?)""",
                    test_user['id'], test_categories[0]['id'], -50,
                    f'Transaction {i}', datetime.now()
                )
        
        # Test first page
        response = authenticated_client.get('/transactions?page=1')
        assert response.status_code == 200
        
        # Test second page
        response = authenticated_client.get('/transactions?page=2')
        assert response.status_code == 200
    
    def test_currency_conversion(self, authenticated_client, test_categories):
        """Test adding transaction with currency conversion."""
        response = authenticated_client.post('/transactions/add', data={
            'amount': '100.00',
            'category_id': test_categories[0]['id'],
            'description': 'EUR transaction',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'currency': 'EUR'
        }, follow_redirects=True)
        
        # Should succeed even with different currency
        assert response.status_code == 200