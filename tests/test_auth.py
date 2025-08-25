"""
Test suite for authentication functionality.

Tests user registration, login, logout, password reset, and session management.
"""

import pytest
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash

class TestRegistration:
    """Test user registration functionality."""
    
    def test_registration_page_loads(self, client):
        """Test that registration page loads successfully."""
        response = client.get('/register')
        assert response.status_code == 200
        assert b'Create Account' in response.data
    
    def test_successful_registration(self, client):
        """Test successful user registration."""
        response = client.post('/register', data={
            'username': 'newuser123',
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
            'terms_accepted': True
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Registration successful' in response.data
        
        # Verify user was created in database
        user = db.execute("SELECT * FROM users WHERE username = ?", 'newuser123')
        assert len(user) == 1
        assert user[0]['email'] == 'newuser@example.com'
    
    def test_duplicate_username(self, client, test_user):
        """Test registration with existing username."""
        response = client.post('/register', data={
            'username': test_user['username'],
            'email': 'different@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
            'terms_accepted': True
        }, follow_redirects=True)
        
        assert b'Username or email already exists' in response.data
    
    def test_weak_password(self, client):
        """Test registration with weak password."""
        response = client.post('/register', data={
            'username': 'weakpassuser',
            'email': 'weak@example.com',
            'password': 'weak',
            'confirm_password': 'weak',
            'terms_accepted': True
        }, follow_redirects=True)
        
        assert b'Password must be at least 8 characters' in response.data
    
    def test_password_mismatch(self, client):
        """Test registration with mismatched passwords."""
        response = client.post('/register', data={
            'username': 'mismatchuser',
            'email': 'mismatch@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'DifferentPass123!',
            'terms_accepted': True
        }, follow_redirects=True)
        
        assert b'Passwords must match' in response.data

class TestLogin:
    """Test user login functionality."""
    
    def test_login_page_loads(self, client):
        """Test that login page loads successfully."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Login' in response.data
    
    def test_successful_login(self, client, test_user):
        """Test successful user login."""
        response = client.post('/login', data={
            'username': test_user['username'],
            'password': test_user['password'],
            'remember_me': False
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Login successful' in response.data or b'Dashboard' in response.data
    
    def test_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials."""
        response = client.post('/login', data={
            'username': test_user['username'],
            'password': 'WrongPassword123!',
            'remember_me': False
        }, follow_redirects=True)
        
        assert b'Invalid username or password' in response.data
    
    def test_unverified_email(self, client):
        """Test login with unverified email."""
        # Create user with unverified email
        username = 'unverified_user'
        email = 'unverified@example.com'
        password = 'TestPass123!'
        
        db.execute("""
            INSERT INTO users (username, email, password_hash, email_verified)
            VALUES (?, ?, ?, FALSE)
        """, username, email, generate_password_hash(password))
        
        response = client.post('/login', data={
            'username': username,
            'password': password,
            'remember_me': False
        }, follow_redirects=True)
        
        assert b'verify your email' in response.data.lower()

class TestLogout:
    """Test user logout functionality."""
    
    def test_successful_logout(self, authenticated_client):
        """Test successful logout."""
        response = authenticated_client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'successfully logged out' in response.data.lower()
        
        # Verify user can't access protected pages
        response = authenticated_client.get('/dashboard')
        assert response.status_code == 302  # Redirect to login

class TestPasswordReset:
    """Test password reset functionality."""
    
    def test_forgot_password_page(self, client):
        """Test that forgot password page loads."""
        response = client.get('/forgot-password')
        assert response.status_code == 200
        assert b'Reset' in response.data
    
    def test_password_reset_request(self, client, test_user):
        """Test password reset request."""
        response = client.post('/forgot-password', data={
            'email': test_user['email']
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'password reset link has been sent' in response.data.lower()
        
        # Verify reset token was created
        user = db.execute(
            "SELECT password_reset_token FROM users WHERE email = ?",
            test_user['email']
        )
        assert user[0]['password_reset_token'] is not None

    def test_password_reset_with_valid_token(self, client, test_user):
        """Test password reset with valid token."""
        # Simulate the password reset token
        token = test_user['password_reset_token']
        response = client.post(f'/reset-password/{token}', data={
            'new_password': 'NewSecurePass123!',
            'confirm_password': 'NewSecurePass123!'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Password has been reset' in response.data.lower()

    def test_password_reset_with_invalid_token(self, client):
        """Test password reset with invalid token."""
        response = client.post('/reset-password/invalid_token', data={
            'new_password': 'NewSecurePass123!',
            'confirm_password': 'NewSecurePass123!'
        }, follow_redirects=True)

        assert response.status_code == 400
        assert b'Invalid or expired password reset token' in response.data.lower()

    def test_password_reset_with_mismatched_passwords(self, client, test_user):
        """Test password reset with mismatched passwords."""
        token = test_user['password_reset_token']
        response = client.post(f'/reset-password/{token}', data={
            'new_password': 'NewSecurePass123!',
            'confirm_password': 'DifferentPassword123!'
        }, follow_redirects=True)

        assert response.status_code == 400
        assert b'Passwords do not match' in response.data.lower()

    def test_password_reset_with_missing_fields(self, client, test_user):
        """Test password reset with missing fields."""
        token = test_user['password_reset_token']
        response = client.post(f'/reset-password/{token}', data={
            'new_password': 'NewSecurePass123!',
            # Missing confirm_password
        }, follow_redirects=True)

        assert response.status_code == 400
        assert b'Please fill out all fields' in response.data.lower()

    def test_password_reset_with_short_password(self, client, test_user):
        """Test password reset with short password."""
        token = test_user['password_reset_token']
        response = client.post(f'/reset-password/{token}', data={
            'new_password': 'short',
            'confirm_password': 'short'
        }, follow_redirects=True)

        assert response.status_code == 400
        assert b'Password must be at least 8 characters long' in response.data.lower()

    def test_password_reset_with_weak_password(self, client, test_user):
        """Test password reset with weak password."""
        token = test_user['password_reset_token']
        response = client.post(f'/reset-password/{token}', data={
            'new_password': '12345678',
            'confirm_password': '12345678'
        }, follow_redirects=True)

        assert response.status_code == 400
        assert b'Password must include at least one uppercase letter, one lowercase letter, and one number' in response.data.lower()

    def test_password_reset_with_valid_token(self, client, test_user):
        """Test password reset with valid token."""
        token = test_user['password_reset_token']
        response = client.post(f'/reset-password/{token}', data={
            'new_password': 'NewSecurePass123!',
            'confirm_password': 'NewSecurePass123!'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Password has been reset' in response.data.lower()

    def test_password_reset_with_invalid_token(self, client):
        """Test password reset with invalid token."""
        response = client.post('/reset-password/invalid_token', data={
            'new_password': 'NewSecurePass123!',
            'confirm_password': 'NewSecurePass123!'
        }, follow_redirects=True)

        assert response.status_code == 400
        assert b'Invalid or expired password reset token' in response.data.lower()

    def test_password_reset_with_mismatched_passwords(self, client, test_user):
        """Test password reset with mismatched passwords."""
        token = test_user['password_reset_token']
        response = client.post(f'/reset-password/{token}', data={
            'new_password': 'NewSecurePass123!',
            'confirm_password': 'DifferentPassword123!'
        }, follow_redirects=True)

        assert response.status_code == 400
        assert b'Passwords do not match' in response.data.lower()

    def test_password_reset_with_missing_fields(self, client, test_user):
        """Test password reset with missing fields."""
        token = test_user['password_reset_token']
        response = client.post(f'/reset-password/{token}', data={
            'new_password': 'NewSecurePass123!',
            # Missing confirm_password
        }, follow_redirects=True)

        assert response.status_code == 400
        assert b'Please fill out all fields' in response.data.lower()

    def test_password_reset_with_short_password(self, client, test_user):
        """Test password reset with short password."""
        token = test_user['password_reset_token']
        response = client.post(f'/reset-password/{token}', data={
            'new_password': 'short',
            'confirm_password': 'short'
        }, follow_redirects=True)

        assert response.status_code == 400
        assert b'Password must be at least 8 characters long' in response.data.lower()

    def test_password_reset_with_weak_password(self, client, test_user):
        """Test password reset with weak password."""
        token = test_user['password_reset_token']
        response = client.post(f'/reset-password/{token}', data={
            'new_password': '12345678',
            'confirm_password': '12345678'
        }, follow_redirects=True)

        assert response.status_code == 400
        assert b'Password must include at least one uppercase letter, one lowercase letter, and one number' in response.data.lower()

    def test_password_reset_with_valid_token(self, client, test_user):
        """Test password reset with valid token."""
        token = test_user['password_reset_token']
        response = client.post(f'/reset-password/{token}', data={
            'new_password': 'NewSecurePass123!',
            'confirm_password': 'NewSecurePass123!'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Password has been reset' in response.data.lower()

    def test_password_reset_with_invalid_token(self, client):
        """Test password reset with invalid token."""
        response = client.post('/reset-password/invalid_token', data={
            'new_password': 'NewSecurePass123!',
            'confirm_password': 'NewSecurePass123!'
        }, follow_redirects=True)

        assert response.status_code == 400
        assert b'Invalid or expired password reset token' in response.data.lower()

    def test_password_reset_with_mismatched_passwords(self, client, test_user):
        """Test password reset with mismatched passwords."""
        token = test_user['password_reset_token']
        response = client.post(f'/reset-password/{token}', data={
            'new_password': 'NewSecurePass123!',
            'confirm_password': 'DifferentPassword123!'
        }, follow_redirects=True)

        assert response.status_code == 400
        assert b'Passwords do not match' in response.data.lower()

    def test_password_reset_with_missing_fields(self, client, test_user):
        """Test password reset with missing fields."""
        token = test_user['password_reset_token']
        response = client.post(f'/reset-password/{token}', data={
            'new_password': 'NewSecurePass123!',
            # Missing confirm_password
        }, follow_redirects=True)

        assert response.status_code == 400
        assert b'Please fill out all fields' in response.data.lower()

    def test_password_reset_with_short_password(self, client, test_user):
        """Test password reset with short password."""
        token = test_user['password_reset_token']
        response = client.post(f'/reset-password/{token}', data={
            'new_password': 'short',
            'confirm_password': 'short'
        }, follow_redirects=True)

        assert response.status_code == 400
        assert b'Password must be at least 8 characters long' in response.data.lower()

    def test_password_reset_with_weak_password(self, client, test_user):
        """Test password reset with weak password."""
        token = test_user['password_reset_token']
        response = client.post(f'/reset-password/{token}', data={
            'new_password': '12345678',
            'confirm_password': '12345678'
        }, follow_redirects=True)

        assert response.status_code == 400
        assert b'Password must include at least one uppercase letter, one lowercase letter, and one number' in response.data.lower()
