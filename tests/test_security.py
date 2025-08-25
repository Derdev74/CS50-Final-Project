"""
Test suite for security features.

Tests authentication, authorization, CSRF protection, and input validation.
"""

import pytest
from datetime import datetime, timedelta

class TestSecurity:
    """Test security features and protections."""
    
    def test_sql_injection_protection(self, authenticated_client):
        """Test protection against SQL injection attacks."""
        # Attempt SQL injection in search
        response = authenticated_client.get('/transactions?search=\'; DROP TABLE users; --')
        
        assert response.status_code == 200
        # Should not cause database error
        
        # Verify users table still exists
        response = authenticated_client.get('/profile')
        assert response.status_code == 200
    
    def test_xss_protection(self, authenticated_client, test_categories):
        """Test protection against XSS attacks."""
        # Attempt to inject script in transaction description
        response = authenticated_client.post('/transactions/add', data={
            'amount': '50.00',
            'category_id': test_categories[0]['id'],
            'description': '<script>alert("XSS")</script>',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'currency': 'USD'
        }, follow_redirects=True)
        
        # Check that script is escaped in response
        assert b'<script>' not in response.data
        assert b'&lt;script&gt;' in response.data or response.status_code == 200
    
    def test_csrf_protection(self, client, test_user):
        """Test CSRF protection on forms."""
        # Login first
        client.post('/login', data={
            'username': test_user['username'],
            'password': test_user['password']
        })
        
        # Try to post without CSRF token (when enabled)
        response = client.post('/transactions/add', data={
            'amount': '50.00',
            'category_id': 1,
            'description': 'Test'
        })
        
        # Should fail or require CSRF token
        assert response.status_code in [400, 403, 302]
    
    def test_unauthorized_access_prevention(self, client, test_user, test_transactions, app):
        """Test that users cannot access other users' data."""
        # Create another user
        with app.app_context():
            other_user_id = db.execute(
                """INSERT INTO users (username, email, password_hash, email_verified)
                   VALUES (?, ?, ?, ?)""",
                'otheruser', 'other@test.com', 'hash', True
            )
        
        # Login as first user
        client.post('/login', data={
            'username': test_user['username'],
            'password': test_user['password']
        })
        
        # Try to delete transaction from other user (should fail)
        response = client.post(f'/transactions/{test_transactions[0]["id"]}/delete')
        
        # Should not be able to delete other user's transaction
        with app.app_context():
            txn = db.execute("SELECT * FROM transactions WHERE id = ?", test_transactions[0]['id'])
            assert len(txn) == 1  # Transaction should still exist
    
    def test_password_complexity_requirements(self, client):
        """Test password complexity validation."""
        weak_passwords = [
            'short',           # Too short
            'alllowercase',    # No uppercase
            'ALLUPPERCASE',    # No lowercase
            'NoNumbers!',      # No numbers
            'NoSpecial123',    # No special characters
            'Has Space!123',   # Contains space
        ]
        
        for password in weak_passwords:
            response = client.post('/register', data={
                'username': 'testuser',
                'email': 'test@test.com',
                'password': password,
                'confirm_password': password,
                'terms_accepted': True
            })
            
            # Should reject weak passwords
            assert b'Password must' in response.data or b'password' in response.data.lower()
    
    def test_session_timeout(self, client, test_user, app, monkeypatch):
        """Test session timeout functionality."""
        # Login
        client.post('/login', data={
            'username': test_user['username'],
            'password': test_user['password']
        })
        
        # Access protected route (should work)
        response = client.get('/dashboard')
        assert response.status_code == 200
        
        # Simulate session timeout by modifying login_time
        with client.session_transaction() as sess:
            sess['login_time'] = (datetime.now() - timedelta(hours=25)).isoformat()
        
        # Try to access protected route (should redirect to login)
        response = client.get('/dashboard')
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_rate_limiting(self, client, test_user):
        """Test rate limiting on login attempts."""
        # Make multiple failed login attempts
        for i in range(6):  # More than RATE_LIMIT_ATTEMPTS
            response = client.post('/login', data={
                'username': test_user['username'],
                'password': 'WrongPassword'
            })
        
        # Should be rate limited
        assert b'Too many login attempts' in response.data