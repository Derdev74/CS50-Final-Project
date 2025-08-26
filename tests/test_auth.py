"""
Test suite for authentication functionality.

Tests user registration, login, logout, password reset, and session management.
"""

import pytest
from werkzeug.security import check_password_hash

class TestAuthentication:
    """Test authentication routes and functionality."""
    
    def test_register_new_user(self, client, app):
        """Test successful user registration."""
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
            'terms_accepted': True
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify user was created in database
        with app.app_context():
            user = db.execute(
                "SELECT * FROM users WHERE username = ?", 
                'newuser'
            )
            assert user is not None
            assert user[0]['email'] == 'newuser@test.com'
    
    def test_register_duplicate_username(self, client, test_user):
        """Test registration with existing username."""
        response = client.post('/register', data={
            'username': test_user['username'],
            'email': 'different@test.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
            'terms_accepted': True
        })
        
        assert b'already exists' in response.data
    
    def test_register_weak_password(self, client):
        """Test registration with weak password."""
        response = client.post('/register', data={
            'username': 'weakpassuser',
            'email': 'weak@test.com',
            'password': 'weak',
            'confirm_password': 'weak',
            'terms_accepted': True
        })
        
        assert b'Password must' in response.data
    
    def test_login_valid_credentials(self, client, test_user):
        """Test login with valid credentials."""
        response = client.post('/login', data={
            'username': test_user['username'],
            'password': test_user['password']
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Dashboard' in response.data or b'dashboard' in response.data
    
    def test_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials."""
        response = client.post('/login', data={
            'username': test_user['username'],
            'password': 'WrongPassword'
        })
        
        assert b'Invalid' in response.data or b'invalid' in response.data
    
    def test_logout(self, authenticated_client):
        """Test user logout."""
        response = authenticated_client.get('/logout', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'logged out' in response.data.lower()
    
    def test_protected_route_requires_login(self, client):
        """Test that protected routes require authentication."""
        routes = ['/dashboard', '/transactions', '/budget', '/goals', '/profile']
        
        for route in routes:
            response = client.get(route)
            assert response.status_code == 302  # Redirect to login
            assert '/login' in response.location
    
    def test_session_persistence(self, client, test_user):
        """Test that session persists across requests."""
        # Login
        client.post('/login', data={
            'username': test_user['username'],
            'password': test_user['password']
        })
        
        # Access protected route
        response = client.get('/dashboard')
        assert response.status_code == 200
        
        # Access another protected route
        response = client.get('/transactions')
        assert response.status_code == 200
    
    def test_password_reset_request(self, client, test_user):
        """Test password reset request."""
        response = client.post('/forgot-password', data={
            'email': test_user['email']
        })
        
        assert response.status_code == 200
        assert b'reset link has been sent' in response.data.lower()
    
    def test_account_lockout_after_failed_attempts(self, client, test_user, app):
        """Test account lockout after multiple failed login attempts."""
        # Simulate multiple failed login attempts
        for i in range(11):  # More than ACCOUNT_LOCKOUT_ATTEMPTS
            client.post('/login', data={
                'username': test_user['username'],
                'password': 'WrongPassword'
            })
        
        # Verify account is locked
        with app.app_context():
            user = db.execute(
                "SELECT locked_until FROM users WHERE username = ?",
                test_user['username']
            )
            assert user[0]['locked_until'] is not None