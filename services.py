"""
services.py
Service classes for authentication and user management logic.
"""

from werkzeug.security import generate_password_hash, check_password_hash
from flask import session
import re
from datetime import datetime, timedelta

class UserService:
    """
    Handles user data operations: lookup, registration, password reset, etc.
    """
    def __init__(self, db):
        self.db = db

    def get_user_by_username(self, username):
        return self.db.execute("SELECT * FROM users WHERE username = ?", username)

    def get_user_by_email(self, email):
        return self.db.execute("SELECT * FROM users WHERE email = ?", email)

    def get_user_by_id(self, user_id):
        return self.db.execute("SELECT * FROM users WHERE id = ?", user_id)

    def create_user(self, username, email, password):
        """Create a new user with hashed password"""
        password_hash = generate_password_hash(password)
        return self.db.execute(
        "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
        username, email, password_hash
        )

    def update_password(self, user_id, new_password):
        """Update user password"""
        password_hash = generate_password_hash(new_password)
        self.db.execute("UPDATE users SET password_hash = ? WHERE id = ?", password_hash, user_id)

    def update_failed_login_attempts(self, username, reset=False):
        """Update failed login attempts for a user"""
        if reset:
            self.db.execute(
                "UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE username = ?",
                username
            )
        else:
            self.db.execute(
                "UPDATE users SET failed_login_attempts = failed_login_attempts + 1 WHERE username = ?",
                username
            )

    def lock_account(self, username, locked_until):
        """Lock user account until specified time"""
        self.db.execute(
            "UPDATE users SET locked_until = ? WHERE username = ?",
            locked_until.isoformat(), username
        )

    def update_last_login(self, user_id):
        """Update last login timestamp"""
        self.db.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            datetime.now().isoformat(), user_id
        )

class AuthService:
    """
    Handles authentication logic: login, password validation, rate limiting, session management.
    """
    def __init__(self, user_service):
        self.user_service = user_service
        self.login_attempts = {}
        self.LOCKOUT_THRESHOLD = 10
        self.LOCKOUT_TIME = 1800  # 30 minutes in seconds

    def validate_password(self, password):
        """Validate password strength"""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        if len(password) > 128:
            errors.append("Password must be less than 128 characters long")
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        if not re.search(r'[0-9]', password):
            errors.append("Password must contain at least one number")
        if not re.search(r'[^A-Za-z0-9]', password):
            errors.append("Password must contain at least one special character")
        if re.search(r'\s', password):
            errors.append("Password cannot contain spaces")
        
        return errors

    def check_password(self, user, password):
        """Check if password matches user's hashed password"""
        return check_password_hash(user["password_hash"], password)

    def login(self, username, password):
        """Authenticate user and return success/error"""
        # Get user from database
        users = self.user_service.get_user_by_username(username)
        
        # Check if user exists
        if not users or len(users) == 0:
            return False, "Invalid username or password."
        
        # Get first user from list (since db.execute returns a list)
        user = users[0]
        
        # Check if account is locked
        if user.get('locked_until'):
            locked_until = datetime.fromisoformat(user['locked_until'])
            if datetime.now() < locked_until:
                remaining_minutes = int((locked_until - datetime.now()).total_seconds() / 60)
                return False, f"Account is temporarily locked. Please try again in {remaining_minutes} minutes."
            else:
                # Unlock account if lock period has expired
                self.user_service.update_failed_login_attempts(username, reset=True)
        
        # Verify password
        if not self.check_password(user, password):
            # Record failed attempt
            self.user_service.update_failed_login_attempts(username)
            
            # Check if we should lock the account
            if user['failed_login_attempts'] + 1 >= self.LOCKOUT_THRESHOLD:
                locked_until = datetime.now().replace(microsecond=0)
                locked_until = locked_until.replace(second=locked_until.second + self.LOCKOUT_TIME)
                self.user_service.lock_account(username, locked_until)
                return False, "Too many failed login attempts. Account has been temporarily locked."
            
            return False, "Invalid username or password."
        
        # Successful login - reset failed attempts and update last login
        self.user_service.update_failed_login_attempts(username, reset=True)
        self.user_service.update_last_login(user['id'])
        
        # Return success (let app.py handle session creation)
        return True, None

    def logout(self):
        """Clear session data"""
        session.clear()