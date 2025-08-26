"""
Test suite for data export functionality.

Tests CSV and PDF export features with proper data isolation.
"""


from datetime import datetime, timedelta
from decimal import Decimal
import pytest
import csv
import io

class TestExport:
    """Test data export functionality."""
    
    def test_export_transactions_csv(self, authenticated_client, test_transactions):
        """Test exporting transactions to CSV."""
        response = authenticated_client.get('/export/transactions/csv')
        
        assert response.status_code == 200
        assert response.content_type == 'text/csv'
        assert b'Transaction ID' in response.data
        
        # Parse CSV content
        csv_data = io.StringIO(response.data.decode('utf-8'))
        reader = csv.reader(csv_data)
        rows = list(reader)
        
        # Check headers
        assert 'Transaction ID' in rows[0]
        assert 'Amount' in rows[0]
        
        # Check data rows exist
        assert len(rows) > 1
    
    def test_export_budgets_csv(self, authenticated_client, test_budget):
        """Test exporting budgets to CSV."""
        response = authenticated_client.get('/export/budgets/csv')
        
        assert response.status_code == 200
        assert response.content_type == 'text/csv'
        assert b'Budget ID' in response.data
    
    def test_export_goals_csv(self, authenticated_client, test_goal):
        """Test exporting goals to CSV."""
        response = authenticated_client.get('/export/goals/csv')
        
        assert response.status_code == 200
        assert response.content_type == 'text/csv'
        assert b'Goal ID' in response.data
    
    def test_export_report_pdf(self, authenticated_client, test_user):
        """Test generating comprehensive PDF report."""
        response = authenticated_client.get('/export/report/pdf')
        
        assert response.status_code == 200
        assert response.content_type == 'application/pdf'
        assert response.data[:4] == b'%PDF'  # PDF magic number
    
    def test_export_with_filters(self, authenticated_client, test_transactions):
        """Test exporting transactions with date filters."""
        date_from = datetime.now().strftime('%Y-%m-%d')
        response = authenticated_client.get(f'/export/transactions/csv?from={date_from}')
        
        assert response.status_code == 200
        assert response.content_type == 'text/csv'
    
    def test_export_rate_limiting(self, authenticated_client, monkeypatch):
        """Test export rate limiting (if implemented)."""
        # Simulate multiple export attempts
        for i in range(12):  # More than EXPORT_RATE_LIMIT
            response = authenticated_client.get('/export/transactions/csv')
            
            if i >= 10:  # Should hit rate limit
                assert b'Export limit exceeded' in response.data or response.status_code == 429
                break