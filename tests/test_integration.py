"""
Integration tests for complete user workflows.

Tests end-to-end scenarios combining multiple features.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

class TestIntegration:
    """Test complete user workflows and feature integration."""
    
    def test_complete_budget_workflow(self, authenticated_client, test_categories, test_user, app):
        """Test creating budget, adding transactions, and viewing spending."""
        expense_category = next(c for c in test_categories if c['type'] == 'expense')
        
        # Create a budget
        authenticated_client.post('/budget/add', data={
            'category_id': expense_category['id'],
            'amount': '500.00',
            'period': 'monthly',
            'start_date': datetime.now().strftime('%Y-%m-%d')
        })
        
        # Add transactions in that category
        for i in range(3):
            authenticated_client.post('/transactions/add', data={
                'amount': '50.00',
                'category_id': expense_category['id'],
                'description': f'Expense {i}',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'currency': 'USD'
            })
        
        # View budget page
        response = authenticated_client.get('/budget')
        assert response.status_code == 200
        
        # Should show spending (150) against budget (500)
        assert b'150' in response.data
        assert b'500' in response.data
    
    def test_goal_tracking_workflow(self, authenticated_client, test_user, app):
        """Test creating goal, updating progress, and achieving it."""
        # Create a goal
        authenticated_client.post('/goal/add', data={
            'name': 'Test Savings',
            'target_amount': '1000.00',
            'initial_amount': '0',
            'deadline': (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d'),
            'goal_type': 'savings'
        })
        
        # Get goal ID
        with app.app_context():
            goal = db.execute(
                "SELECT id FROM goals WHERE user_id = ? AND name = ?",
                test_user['id'], 'Test Savings'
            )[0]
        
        # Add progress in increments
        for amount in ['250.00', '250.00', '250.00', '250.00']:
            response = authenticated_client.post(
                f'/goal/{goal["id"]}/update',
                data={'amount': amount, 'action': 'add'},
                follow_redirects=True
            )
        
        # Should show goal completed
        assert b'Congratulations' in response.data
    
    def test_multi_currency_workflow(self, authenticated_client, test_categories, test_user, app):
        """Test handling multiple currencies in transactions."""
        # Update user's preferred currency
        authenticated_client.post('/profile/preferences', data={
            'theme': 'light',
            'preferred_currency': 'EUR'
        })
        
        # Add transactions in different currencies
        currencies = ['USD', 'EUR', 'GBP']
        for currency in currencies:
            response = authenticated_client.post('/transactions/add', data={
                'amount': '100.00',
                'category_id': test_categories[0]['id'],
                'description': f'{currency} transaction',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'currency': currency
            }, follow_redirects=True)
            
            assert response.status_code == 200
        
        # View transactions - should show conversions
        response = authenticated_client.get('/transactions')
        assert response.status_code == 200
        assert b'EUR' in response.data
    
    def test_data_export_workflow(self, authenticated_client, test_transactions, test_budget, test_goal):
        """Test exporting all data types."""
        # Export transactions
        response = authenticated_client.get('/export/transactions/csv')
        assert response.status_code == 200
        assert b'Transaction ID' in response.data
        
        # Export budgets
        response = authenticated_client.get('/export/budgets/csv')
        assert response.status_code == 200
        assert b'Budget ID' in response.data
        
        # Export goals
        response = authenticated_client.get('/export/goals/csv')
        assert response.status_code == 200
        assert b'Goal ID' in response.data
        
        # Generate PDF report
        response = authenticated_client.get('/export/report/pdf')
        assert response.status_code == 200
        assert response.data[:4] == b'%PDF'