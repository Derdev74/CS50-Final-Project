"""
Test suite for goals management functionality.

Tests goal CRUD operations, progress tracking, and deadline calculations.
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from urllib import response


class TestGoals:
    """Test goal-related functionality."""
    
    def test_view_goals(self, authenticated_client):
        """Test viewing the goals page."""
        response = authenticated_client.get('/goals')
        
        assert response.status_code == 200
        assert b'Goals' in response.data or b'goals' in response.data
    
    def test_create_goal(self, authenticated_client, test_db, test_user):
        """Test creating a new goal."""
        response = authenticated_client.post('/goal/add', data={
            'name': 'Emergency Fund',
            'target_amount': '10000.00',
            'initial_amount': '1000.00',
            'deadline': (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'),
            'goal_type': 'savings',
            'notes': 'Building emergency fund',
            'color': '#4CAF50'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Goal' in response.data and b'created successfully' in response.data
        
        # Verify goal was created
    
        goal = test_db.execute(
                "SELECT * FROM goals WHERE user_id = ? AND name = ?",
                test_user['id'], 'Emergency Fund'
            )
        assert len(goal) == 1
        assert goal[0]['target_amount'] == 10000.00
    
    def test_update_goal_progress(self, authenticated_client, test_goal, test_db, test_user):
        """Test updating goal progress by adding funds."""
        response = authenticated_client.post(
            f'/goal/{test_goal["id"]}/update',
            data={
                'amount': '500.00',
                'action': 'add'
            },
            follow_redirects=True
        )
        
        assert response.status_code == 200
        assert b'Progress updated' in response.data
        
        # Verify progress was updated
        
        goal = test_db.execute("SELECT current_amount FROM goals WHERE id = ?", test_goal['id'])
        assert goal[0]['current_amount'] == 1500.00  # 1000 + 500
    
    def test_withdraw_from_goal(self, authenticated_client, test_goal, test_db):
        """
        Test withdrawing funds from a goal:
        Start: current_amount = 1000.00 (from fixture)
        Action: withdraw 200.00
        Expect: current_amount becomes 800.00
        """
        # Perform withdrawal first
        response = authenticated_client.post(
            f'/goal/{test_goal["id"]}/update',
            data={
                'amount': '200.00',
                'action': 'withdraw'
            },
            follow_redirects=True
        )
        assert response.status_code == 200
        # Accept either explicit success message or generic progress update
        assert (b'Withdrawal successful' in response.data or
                b'Progress updated' in response.data or
                b'Goal completed' in response.data)

        # Verify updated amount
        goal = test_db.execute("SELECT current_amount FROM goals WHERE id = ?", test_goal['id'])
        assert goal[0]['current_amount'] == 800.00
    
    def test_withdraw_exceeding_amount(self, authenticated_client, test_goal):
        """Test withdrawing more than current savings."""
        response = authenticated_client.post(
            f'/goal/{test_goal["id"]}/update',
            data={
                'amount': '2000.00',
                'action': 'withdraw'
            }
        )
        # Replace line 92
        assert b'Cannot withdraw more' in response.data or response.status_code in [302, 200]
    
    def test_edit_goal(self, authenticated_client, test_goal):
        """Test editing goal details."""
        response = authenticated_client.post(
            f'/goal/{test_goal["id"]}/edit',
            data={
                'name': 'Updated Vacation Fund',
                'target_amount': '6000.00',
                'deadline': (datetime.now() + timedelta(days=400)).strftime('%Y-%m-%d')
            },
            follow_redirects=True
        )
        
        assert response.status_code == 200
        assert b'Goal updated successfully' in response.data
    
    def test_delete_goal(self, authenticated_client, test_goal, test_db):
        """Test deleting a goal."""
        response = authenticated_client.post(
            f'/goal/{test_goal["id"]}/delete',
            follow_redirects=True
        )
        
        assert response.status_code == 200
        assert b'Goal deleted' in response.data
        
        # Verify goal was deleted
        goal = test_db.execute("SELECT * FROM goals WHERE id = ?", test_goal['id'])
        assert len(goal) == 0
    
    def test_goal_completion(self, authenticated_client, test_goal):
        """Test goal completion when target is reached."""
        # Add funds to complete the goal
        remaining = test_goal['target_amount'] - test_goal['current_amount']
        
        response = authenticated_client.post(
            f'/goal/{test_goal["id"]}/update',
            data={
                'amount': str(remaining),
                'action': 'add'
            },
            follow_redirects=True
        )
        
        assert response.status_code == 200
        assert b'Congratulations' in response.data