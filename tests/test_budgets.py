"""
Test suite for budget management functionality.

Tests budget CRUD operations, spending tracking, and period calculations.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

class TestBudgets:
    """Test budget-related functionality."""
    
    def test_view_budgets(self, authenticated_client):
        """Test viewing the budgets page."""
        response = authenticated_client.get('/budget')
        
        assert response.status_code == 200
        assert b'Budget' in response.data
    
    def test_create_budget(self, authenticated_client, test_categories, app, test_user):
        """Test creating a new budget."""
        expense_category = next(c for c in test_categories if c['type'] == 'expense')
        
        response = authenticated_client.post('/budget/add', data={
            'category_id': expense_category['id'],
            'amount': '500.00',
            'period': 'monthly',
            'start_date': datetime.now().strftime('%Y-%m-%d')
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Budget created successfully' in response.data
        
        # Verify budget was created
        with app.app_context():
            budget = db.execute(
                "SELECT * FROM budgets WHERE user_id = ? AND category_id = ?",
                test_user['id'], expense_category['id']
            )
            assert len(budget) == 1
            assert budget[0]['amount'] == 500.00
    
    def test_create_duplicate_budget(self, authenticated_client, test_budget):
        """Test creating duplicate budget for same category/period."""
        response = authenticated_client.post('/budget/add', data={
            'category_id': test_budget['category_id'],
            'amount': '600.00',
            'period': test_budget['period'],
            'start_date': datetime.now().strftime('%Y-%m-%d')
        })
        
        assert b'already exists' in response.data
    
    def test_edit_budget(self, authenticated_client, test_budget):
        """Test editing a budget amount."""
        response = authenticated_client.post(
            f'/budget/{test_budget["id"]}/edit',
            data={'amount': '750.00'},
            follow_redirects=True
        )
        
        assert response.status_code == 200
        assert b'Budget updated successfully' in response.data
    
    def test_delete_budget(self, authenticated_client, test_budget, app):
        """Test deleting a budget."""
        response = authenticated_client.post(
            f'/budget/{test_budget["id"]}/delete',
            follow_redirects=True
        )
        
        assert response.status_code == 200
        assert b'Budget deleted successfully' in response.data
        
        # Verify budget was deleted
        with app.app_context():
            budget = db.execute("SELECT * FROM budgets WHERE id = ?", test_budget['id'])
            assert len(budget) == 0
    
    def test_budget_spending_calculation(self, authenticated_client, test_budget, test_user, app):
        """Test that budget spending is calculated correctly."""
        # Add a transaction in the budget category
        with app.app_context():
            db.execute(
                """INSERT INTO transactions (user_id, category_id, amount, date)
                   VALUES (?, ?, ?, ?)""",
                test_user['id'], test_budget['category_id'], -200,
                datetime.now()
            )
        
        response = authenticated_client.get('/budget')
        assert response.status_code == 200
        # Should show spending against budget
        assert b'200' in response.data
    
    def test_budget_period_calculations(self, authenticated_client, test_categories, test_user):
        """Test different budget periods (weekly, monthly, yearly)."""
        periods = ['weekly', 'monthly', 'yearly']
        
        for period in periods:
            response = authenticated_client.post('/budget/add', data={
                'category_id': test_categories[0]['id'],
                'amount': '1000.00',
                'period': period,
                'start_date': datetime.now().strftime('%Y-%m-%d')
            })
            
            # Should handle all period types
            assert response.status_code in [200, 302]