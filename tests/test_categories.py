"""
Test suite for user-defined categories functionality.

Tests category CRUD operations and integration with transactions.
"""

from app import db
import pytest

class TestCategories:
    """Test user-defined categories functionality."""
    
    def test_view_categories(self, authenticated_client):
        """Test viewing the categories management page."""
        response = authenticated_client.get('/categories')
        
        assert response.status_code == 200
        assert b'Category Management' in response.data
    
    def test_create_user_category(self, authenticated_client, app, test_user):
        """Test creating a user-defined category."""
        response = authenticated_client.post('/categories/add', data={
            'name': 'Custom Category',
            'type': 'expense',
            'color': '#FF5733',
            'icon': 'shopping-cart'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Category' in response.data and b'created successfully' in response.data
        
        # Verify category was created
        with app.app_context():
            category = db.execute(
                "SELECT * FROM user_categories WHERE user_id = ? AND name = ?",
                test_user['id'], 'Custom Category'
            )
            assert len(category) == 1
            assert category[0]['color'] == '#FF5733'
    
    def test_create_duplicate_category(self, authenticated_client, test_user, app):
        """Test creating duplicate category name."""
        # Create first category
        with app.app_context():
            db.execute(
                """INSERT INTO user_categories (user_id, name, type, color, icon)
                   VALUES (?, ?, ?, ?, ?)""",
                test_user['id'], 'Duplicate Test', 'expense', '#000000', 'folder'
            )
        
        # Try to create duplicate
        response = authenticated_client.post('/categories/add', data={
            'name': 'Duplicate Test',
            'type': 'expense',
            'color': '#FFFFFF',
            'icon': 'folder'
        })
        
        assert b'already exists' in response.data
    
    def test_edit_user_category(self, authenticated_client, test_user, app):
        """Test editing a user-defined category."""
        # Create a category first
        with app.app_context():
            cat_id = db.execute(
                """INSERT INTO user_categories (user_id, name, type, color, icon)
                   VALUES (?, ?, ?, ?, ?)""",
                test_user['id'], 'Edit Test', 'income', '#000000', 'folder'
            )
        
        response = authenticated_client.post(
            f'/categories/{cat_id}/edit',
            data={
                'name': 'Edited Category',
                'color': '#FF0000',
                'icon': 'briefcase',
                'is_active': 'true'
            },
            follow_redirects=True
        )
        
        assert response.status_code == 200
        assert b'Category updated successfully' in response.data
    
    def test_delete_user_category(self, authenticated_client, test_user, app):
        """Test deleting a user-defined category."""
        # Create a category first
        with app.app_context():
            cat_id = db.execute(
                """INSERT INTO user_categories (user_id, name, type, color, icon)
                   VALUES (?, ?, ?, ?, ?)""",
                test_user['id'], 'Delete Test', 'expense', '#000000', 'folder'
            )
        
        response = authenticated_client.post(
            f'/categories/{cat_id}/delete',
            follow_redirects=True
        )
        
        assert response.status_code == 200
        assert b'Category deleted successfully' in response.data
        
        # Verify deletion
        with app.app_context():
            category = db.execute(
                "SELECT * FROM user_categories WHERE id = ?", cat_id
            )
            assert len(category) == 0