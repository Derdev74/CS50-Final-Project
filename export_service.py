""":
Export Service Module for FinTrack Application

This module provides comprehensive data export functionality, allowing users
to download their financial data in various formats (CSV, PDF) for backup,
analysis, or sharing purposes.

Security considerations:
- Users can only export their own data
- Export requests are logged for audit purposes
- File generation is done in memory to avoid disk storage
- Sanitization of data to prevent injection attacks
"""
import csv
import io
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

logger = logging.getLogger(__name__)

def build_csv(filename_prefix, header, rows_iter):
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(header)
    for row in rows_iter:
        w.writerow(row)
    fname = f"{filename_prefix}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
    return fname, out.getvalue().encode('utf-8')

class ExportService:
    """
    Service class for handling data exports in various formats.
    
    This service provides methods to export user financial data to CSV and PDF formats,
    with proper formatting, security checks, and comprehensive data inclusion.
    """
    
    def __init__(self, db):
        """
        Initialize the export service.
        
        Args:
            db: Database connection object
        """
        self.db = db
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Set up custom PDF styles for better formatting."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#34495E'),
            spaceAfter=12,
            spaceBefore=12
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        ))
    
    def export_transactions_csv(self, user_id: int, filters: Optional[Dict] = None) -> io.StringIO:
        """
        Export user transactions to CSV format.
        
        Args:
            user_id: ID of the user whose transactions to export
            filters: Optional filters (date range, category, etc.)
            
        Returns:
            StringIO object containing CSV data
            
        Security:
        - Only exports transactions belonging to the specified user
        - Sanitizes data to prevent CSV injection
        """
        try:
            # Build query with filters
            query = """
                SELECT 
                    t.id,
                    t.date,
                    c.name as category,
                    c.type as type,
                    t.description,
                    t.amount,
                    t.currency,
                    t.original_amount,
                    t.exchange_rate
                FROM transactions t
                LEFT JOIN categories c ON t.category_id = c.id
                WHERE t.user_id = ?
            """
            params = [user_id]
            
            # Apply filters if provided
            if filters:
                if filters.get('date_from'):
                    query += " AND DATE(t.date) >= ?"
                    params.append(filters['date_from'])
                if filters.get('date_to'):
                    query += " AND DATE(t.date) <= ?"
                    params.append(filters['date_to'])
                if filters.get('category_id'):
                    query += " AND t.category_id = ?"
                    params.append(filters['category_id'])
            
            query += " ORDER BY t.date DESC"
            
            transactions = self.db.execute(query, *params)
            
            # Create CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            headers = [
                'Transaction ID',
                'Date',
                'Category',
                'Type',
                'Description',
                'Amount',
                'Currency',
                'Original Amount',
                'Exchange Rate'
            ]
            writer.writerow(headers)
            
            # Write transaction data
            for txn in transactions:
                row = [
                    txn['id'],
                    txn['date'][:10] if txn['date'] else '',
                    self._sanitize_csv_field(txn['category'] or 'Uncategorized'),
                    txn['type'] or 'expense',
                    self._sanitize_csv_field(txn['description'] or ''),
                    f"{abs(txn['amount']):.2f}",
                    txn['currency'] or 'USD',
                    f"{abs(txn['original_amount']):.2f}" if txn['original_amount'] else '',
                    f"{txn['exchange_rate']:.4f}" if txn['exchange_rate'] else '1.0000'
                ]
                writer.writerow(row)
            
            # Add summary row
            total_income = sum(t['amount'] for t in transactions if t['amount'] > 0)
            total_expense = sum(abs(t['amount']) for t in transactions if t['amount'] < 0)
            writer.writerow([])
            writer.writerow(['Summary', '', '', '', '', '', '', '', ''])
            writer.writerow(['Total Income', '', '', '', '', f"{total_income:.2f}", '', '', ''])
            writer.writerow(['Total Expenses', '', '', '', '', f"{total_expense:.2f}", '', '', ''])
            writer.writerow(['Net Balance', '', '', '', '', f"{total_income - total_expense:.2f}", '', '', ''])
            
            output.seek(0)
            logger.info(f"Exported {len(transactions)} transactions to CSV for user {user_id}")
            return output
            
        except Exception as e:
            logger.error(f"Error exporting transactions to CSV: {str(e)}")
            raise
    
    def export_budgets_csv(self, user_id: int) -> io.StringIO:
        """
        Export user budgets to CSV format.
        
        Args:
            user_id: ID of the user whose budgets to export
            
        Returns:
            StringIO object containing CSV data
        """
        try:
            # Fetch budgets with spending data
            budgets = self.db.execute("""
                SELECT 
                    b.id,
                    c.name as category,
                    b.amount as budget_amount,
                    b.period,
                    b.start_date,
                    COALESCE(
                        (SELECT SUM(ABS(t.amount))
                         FROM transactions t
                         WHERE t.user_id = b.user_id
                         AND t.category_id = b.category_id
                         AND DATE(t.date) >= DATE('now', 'start of month')),
                        0
                    ) as current_spending
                FROM budgets b
                JOIN categories c ON b.category_id = c.id
                WHERE b.user_id = ?
                ORDER BY b.period, c.name
            """, user_id)
            
            # Create CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            headers = [
                'Budget ID',
                'Category',
                'Budget Amount',
                'Period',
                'Start Date',
                'Current Spending',
                'Remaining',
                'Usage %'
            ]
            writer.writerow(headers)
            
            # Write budget data
            for budget in budgets:
                remaining = budget['budget_amount'] - budget['current_spending']
                usage_pct = (budget['current_spending'] / budget['budget_amount'] * 100) if budget['budget_amount'] > 0 else 0
                
                row = [
                    budget['id'],
                    self._sanitize_csv_field(budget['category']),
                    f"{budget['budget_amount']:.2f}",
                    budget['period'],
                    budget['start_date'],
                    f"{budget['current_spending']:.2f}",
                    f"{remaining:.2f}",
                    f"{usage_pct:.1f}%"
                ]
                writer.writerow(row)
            
            output.seek(0)
            logger.info(f"Exported {len(budgets)} budgets to CSV for user {user_id}")
            return output
            
        except Exception as e:
            logger.error(f"Error exporting budgets to CSV: {str(e)}")
            raise
    
    def export_goals_csv(self, user_id: int) -> io.StringIO:
        """
        Export user goals to CSV format.
        
        Args:
            user_id: ID of the user whose goals to export
            
        Returns:
            StringIO object containing CSV data
        """
        try:
            goals = self.db.execute("""
                SELECT 
                    id,
                    name,
                    target_amount,
                    current_amount,
                    deadline,
                    COALESCE(created_at, datetime('now')) as created_at
                FROM goals
                WHERE user_id = ?
                ORDER BY deadline, id
            """, user_id)
            # Create CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            headers = [
                'Goal ID',
                'Name',
                'Target Amount',
                'Current Amount',
                'Progress %',
                'Remaining',
                'Deadline',
                'Days Remaining',
                'Status',
                'Created Date'
            ]
            writer.writerow(headers)
            
            # Write goal data
            current_date = datetime.now().date()
            
            for goal in goals:
                progress = (goal['current_amount'] / goal['target_amount'] * 100) if goal['target_amount'] > 0 else 0
                remaining = goal['target_amount'] - goal['current_amount']
                
                # Calculate days remaining
                days_remaining = 'No deadline'
                status = 'Active'
                if goal['deadline']:
                    deadline_date = datetime.strptime(goal['deadline'], '%Y-%m-%d').date()
                    days = (deadline_date - current_date).days
                    
                    if progress >= 100:
                        status = 'Completed'
                    elif days < 0:
                        status = 'Overdue'
                        days_remaining = f"{abs(days)} days overdue"
                    else:
                        days_remaining = f"{days} days"
                        if days <= 30:
                            status = 'Urgent'
                
                row = [
                    goal['id'],
                    self._sanitize_csv_field(goal['name']),
                    f"{goal['target_amount']:.2f}",
                    f"{goal['current_amount']:.2f}",
                    f"{progress:.1f}%",
                    f"{remaining:.2f}",
                    goal['deadline'] or 'Not set',
                    days_remaining,
                    status,
                    goal['created_at'][:10] if goal['created_at'] else ''
                ]
                writer.writerow(row)
            
            output.seek(0)
            logger.info(f"Exported {len(goals)} goals to CSV for user {user_id}")
            return output
            
        except Exception as e:
            logger.error(f"Error exporting goals to CSV: {str(e)}")
            raise
    
    def export_complete_report_pdf(self, user_id: int, user_info: Dict) -> io.BytesIO:
        """
        Generate a comprehensive PDF report of all user financial data.
        
        Args:
            user_id: ID of the user
            user_info: Dictionary containing user information
            
        Returns:
            BytesIO object containing PDF data
        """
        try:
            # Create PDF in memory
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )
            
            # Container for the 'Flowable' objects
            elements = []
            
            # Title Page
            elements.append(Paragraph(
                "FinTrack Financial Report",
                self.styles['CustomTitle']
            ))
            
            elements.append(Paragraph(
                f"Generated for: {user_info.get('username', 'User')}",
                self.styles['Normal']
            ))
            
            elements.append(Paragraph(
                f"Date: {datetime.now().strftime('%B %d, %Y')}",
                self.styles['Normal']
            ))
            
            elements.append(Spacer(1, 0.5*inch))
            
            # Account Summary Section
            elements.append(Paragraph("Account Summary", self.styles['CustomSubtitle']))
            
            account_data = [
                ['Account Balance:', f"${user_info.get('balance', 0):.2f}"],
                ['Member Since:', user_info.get('created_at', 'N/A')[:10]],
                ['Total Transactions:', str(user_info.get('transaction_count', 0))],
                ['Active Budgets:', str(user_info.get('budget_count', 0))],
                ['Active Goals:', str(user_info.get('goal_count', 0))]
            ]
            
            account_table = Table(account_data, colWidths=[2*inch, 2*inch])
            account_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ]))
            elements.append(account_table)
            elements.append(Spacer(1, 0.3*inch))
            
            # Recent Transactions Section
            elements.append(Paragraph("Recent Transactions", self.styles['CustomSubtitle']))
            
            transactions = self.db.execute("""
                SELECT 
                    t.date,
                    c.name as category,
                    t.description,
                    t.amount,
                    t.currency
                FROM transactions t
                LEFT JOIN categories c ON t.category_id = c.id
                WHERE t.user_id = ?
                ORDER BY t.date DESC
                LIMIT 10
            """, user_id)
            
            if transactions:
                txn_data = [['Date', 'Category', 'Description', 'Amount']]
                for txn in transactions:
                    txn_data.append([
                        txn['date'][:10],
                        (txn['category'] or 'Uncategorized')[:20],
                        (txn['description'] or '')[:30],
                        f"${abs(txn['amount']):.2f}"
                    ])
                
                txn_table = Table(txn_data, colWidths=[1.5*inch, 1.5*inch, 2.5*inch, 1*inch])
                txn_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(txn_table)
            else:
                elements.append(Paragraph("No transactions found.", self.styles['Normal']))
            
            elements.append(PageBreak())
            
            # Budgets Section
            elements.append(Paragraph("Budget Overview", self.styles['CustomSubtitle']))
            
            budgets = self.db.execute("""
                SELECT 
                    c.name as category,
                    b.amount,
                    b.period
                FROM budgets b
                JOIN categories c ON b.category_id = c.id
                WHERE b.user_id = ?
                ORDER BY b.period, c.name
            """, user_id)
            
            if budgets:
                budget_data = [['Category', 'Amount', 'Period']]
                for budget in budgets:
                    budget_data.append([
                        budget['category'],
                        f"${budget['amount']:.2f}",
                        budget['period'].capitalize()
                    ])
                
                budget_table = Table(budget_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
                budget_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(budget_table)
            else:
                elements.append(Paragraph("No budgets configured.", self.styles['Normal']))
            
            elements.append(Spacer(1, 0.3*inch))
            
            # Goals Section
            elements.append(Paragraph("Savings Goals", self.styles['CustomSubtitle']))
            
            goals = self.db.execute("""
                SELECT 
                    id,
                    name,
                    target_amount,
                    current_amount,
                    deadline,
                    COALESCE(created_at, datetime('now')) as created_at
                FROM goals
                WHERE user_id = ?
                ORDER BY deadline, id
            """, user_id)
            if goals:
                goals_data = [['Goal', 'Target', 'Current', 'Progress', 'Deadline']]
                for goal in goals:
                    progress = (goal['current_amount'] / goal['target_amount'] * 100) if goal['target_amount'] > 0 else 0
                    goals_data.append([
                        goal['name'][:25],
                        f"${goal['target_amount']:.2f}",
                        f"${goal['current_amount']:.2f}",
                        f"{progress:.1f}%",
                        goal['deadline'] or 'No deadline'
                    ])
                
                goals_table = Table(goals_data, colWidths=[2*inch, 1.2*inch, 1.2*inch, 1*inch, 1.5*inch])
                goals_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(goals_table)
            else:
                elements.append(Paragraph("No goals configured.", self.styles['Normal']))
            
            # Footer
            elements.append(Spacer(1, 0.5*inch))
            elements.append(Paragraph(
                "This report is confidential and for personal use only.",
                self.styles['Footer']
            ))
            elements.append(Paragraph(
                f"Generated by FinTrack on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                self.styles['Footer']
            ))
            
            # Build PDF
            doc.build(elements)
            buffer.seek(0)
            
            logger.info(f"Generated comprehensive PDF report for user {user_id}")
            return buffer
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            raise
    
    def _sanitize_csv_field(self, value: str) -> str:
        """
        Sanitize CSV field to prevent injection attacks.
        
        Args:
            value: Field value to sanitize
            
        Returns:
            Sanitized string safe for CSV
        """
        if not value:
            return ''
        
        # Remove or escape potentially dangerous characters
        # that could be interpreted as formulas in spreadsheet applications
        if str(value).startswith(('=', '+', '-', '@', '\t', '\r')):
            value = "'" + str(value)
        
        # Replace newlines with spaces
        value = str(value).replace('\n', ' ').replace('\r', ' ')
        
        # Limit length to prevent excessive data
        return value[:500]