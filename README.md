# FinTrack - Personal Finance Management System

## Overview

FinTrack is a comprehensive personal finance web application built as my CS50 final project. It provides a complete solution for managing personal finances with features including transaction tracking, budgeting, goal setting, multi-currency support with real-time conversion, and secure data export capabilities. The application emphasizes security, scalability, and user experience while demonstrating modern web development best practices.

**Built with:** Flask, SQLite, Python | **Security:** OAuth 2.0, CSRF Protection, Rate Limiting | **Testing:** 70+ automated test cases

## Core Features

### 💰 Financial Management
- **Transaction Tracking**: Record and manage income/expense transactions with automatic balance calculation
- **Multi-Currency Support**: Track transactions in 40+ currencies with **CurrencyLayer API** integration for real-time exchange rates
- **Smart Currency Service**: Intelligent rate caching (1-hour duration) with fallback to static rates for offline functionality
- **Budget Management**: Set category-specific budgets with flexible periods (weekly, monthly, yearly) and real-time spending tracking
- **Savings Goals**: Create and track financial goals with progress indicators, deadlines, and withdrawal/contribution management

### 🔐 Security & Authentication
- **Multiple Login Options**: Traditional authentication + **Google OAuth 2.0** integration for passwordless sign-in
- **Password Security**: Strong password requirements (8+ chars, uppercase, lowercase, digits, special characters) with bcrypt hashing
- **Email Verification**: Token-based email verification system with attempt tracking
- **Password Reset**: Secure email-based password reset with 15-minute token expiration
- **Session Protection**: 24-hour session lifetime, IP address validation, and automatic timeout
- **Account Lockout**: Automatic account locking after 10 failed login attempts (30-minute lockout)
- **Rate Limiting**:
  - Login attempts: 5 per 5 minutes
  - Export requests: 10 per hour
  - Email verification and password reset throttling
- **Security Audit Trail**: Comprehensive logging of all security events with timestamps, IP addresses, and user agents
- **CSRF & XSS Protection**: Flask-WTF CSRF tokens on all forms and input sanitization throughout
- **SQL Injection Prevention**: Parameterized queries using CS50's SQL library

### 📊 Data Export & Reporting
- **CSV Exports**: Export transactions, budgets, and goals with filtering options (date range, category)
- **PDF Report Generation**: Comprehensive financial reports using **ReportLab** library with custom formatting
- **Structured Data**: Consistent headers and formatting across all export types
- **Rate-Limited Downloads**: Secure file generation with abuse prevention (10 exports/hour)

### 🎨 User Experience
- **Responsive Dashboard**: Real-time financial overview with balance tracking, quick stats, and visual charts
- **Category Management**: 15 pre-defined system categories + custom user categories with icons and colors
- **Profile Customization**: Light/dark theme toggle, preferred currency selection (40+ supported)
- **Smart Filtering**: Filter transactions by category, date range, and type with pagination
- **Mobile-Friendly**: Bootstrap-based responsive design for all screen sizes

### 🧪 Quality & Testing
- **Comprehensive Test Suite**: 70+ automated test cases across 9 test modules
- **Test Coverage**: Authentication, transactions, budgets, categories, goals, exports, integration, and security tests
- **Code Quality**: Fixtures for deterministic testing, autouse fixtures for state isolation, and pytest-cov integration

## Project Architecture

### Core Application Files

- **`app.py`**: Main Flask application with all route handlers, database initialization, and business logic
- **`helpers.py`**: Helper functions including CurrencyService (API integration, caching), login_required decorator, and utility functions
- **`services.py`**: Service layer with UserService and AuthService for clean separation of concerns
- **`export_service.py`**: Data export functionality (CSV/PDF generation using ReportLab)
- **`oauth_service.py`**: Google OAuth 2.0 integration with token exchange and verification
- **`conftest.py`**: Pytest configuration with test fixtures and sample data seeding

### Database Schema

**9 Tables with optimized indexes:**
- `users`: Authentication, preferences, session management
- `categories` + `user_categories`: System and custom category definitions
- `transactions`: Financial records with multi-currency support
- `budgets`: Category budgets with period tracking
- `goals`: Savings goals with progress tracking
- `security_logs`: Comprehensive audit trail
- `email_verification_attempts`: Rate limiting for verification
- `exchange_rates`: Cached currency conversion rates

### Templates & Assets

- **18 HTML Templates**: Authentication pages, dashboard, transactions, budgets, goals, categories, profile, error pages, email templates
- **Static Files**: CSS for theming, JavaScript for interactive features

### Testing Infrastructure

**9 Test Modules** covering all application functionality:
- Authentication & OAuth flows
- Transaction CRUD operations
- Budget & category management
- Goal tracking workflows
- Data export validation
- Integration scenarios
- Security vulnerability testing

## Key Design Decisions

### 1. **Service Layer Architecture**
Clean separation with `UserService`, `AuthService`, `CurrencyService`, `ExportService`, and `GoogleOAuthService` for testable, maintainable code.

### 2. **CurrencyLayer API Integration**
Real-time exchange rate conversion for 40+ currencies with intelligent caching (1-hour) and fallback to static rates for offline functionality.

### 3. **Security-First Approach**
- Parameterized SQL queries (CS50 SQL library) prevent injection attacks
- Bcrypt password hashing via Werkzeug
- CSRF tokens on all forms (Flask-WTF)
- Comprehensive rate limiting and session management
- Audit logging for all security events

### 4. **ReportLab PDF Generation**
Custom-formatted financial reports with comprehensive data export capabilities, rate-limited to prevent abuse.

### 5. **Google OAuth 2.0**
Secure passwordless authentication with token exchange, ID verification, and CSRF protection via state parameters.

### 6. **Comprehensive Testing**
70+ pytest cases with fixtures for deterministic testing, autouse fixtures for state isolation, and full integration coverage.

## Technology Stack

**Core:** Flask 2.3.3, Python 3.12, SQLite, CS50 SQL Library
**Security:** Werkzeug (bcrypt), Flask-WTF (CSRF), Authlib (OAuth), Google Auth, Flask-Limiter
**Data & Export:** Pandas, ReportLab (PDF), CurrencyLayer API
**Email:** Flask-Mail, SMTP
**Testing:** pytest, pytest-flask, pytest-cov, faker
**Other:** python-dotenv, python-dateutil, requests

## Installation & Setup

### Quick Start

```bash
# 1. Clone and navigate
git clone <repository-url>
cd "Final project"

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt  # Optional, for testing

# 4. Configure environment variables
# Copy .env.example to .env and fill in your credentials
cp .env.example .env

# 5. Run the application (database auto-initializes)
flask run
```

### Environment Variables Setup

**🔒 IMPORTANT:** Never commit your `.env` file! Use `.env.example` as a template.

Required configuration in `.env`:

```bash
# Flask
SECRET_KEY=<generate-with: python -c "import secrets; print(secrets.token_hex(32))">
FLASK_ENV=development

# Email (for password reset & verification)
MAIL_SERVER=smtp.gmail.com
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=<your-gmail-app-password>

# Google OAuth (optional)
GOOGLE_CLIENT_ID=<from-google-console>
GOOGLE_CLIENT_SECRET=<from-google-console>

# CurrencyLayer API (optional)
CURRENCYLAYER_API_KEY=<from-currencylayer.com>
```

### Running Tests

```bash
pytest -v                    # All tests
pytest --cov                 # With coverage
pytest tests/test_auth.py    # Specific module
```

## Usage Overview

1. **Register/Login**: Create account with email verification or use Google OAuth
2. **Dashboard**: View financial overview, balance, recent activity
3. **Transactions**: Add income/expenses in multiple currencies, filter and manage records
4. **Budgets**: Set category budgets with flexible periods, track spending in real-time
5. **Goals**: Create savings goals, track progress, manage contributions
6. **Categories**: Use 15 system categories or create custom ones
7. **Export**: Generate CSV/PDF reports (rate-limited to 10/hour)
8. **Profile**: Customize theme, currency preference, manage account settings

## Future Enhancements

- Enhanced PDF reports with charts and visualizations
- Email notifications for budget limits and goal milestones
- Recurring transactions and automated budgets
- Bank account integration (Plaid API)
- Mobile app (React Native)
- Advanced analytics with ML-powered spending predictions
- Shared budgets for families/roommates
- Investment portfolio tracking
- Additional OAuth providers (GitHub, Apple, Facebook)
- Migration to PostgreSQL + Redis for scalability
- CI/CD pipeline with GitHub Actions

## Known Limitations

- **SQLite**: Suitable for single-user/small-scale. Migrate to PostgreSQL for production.
- **File-based sessions**: Use Redis for distributed deployments.
- **CurrencyLayer free tier**: Has rate limits; upgrade for high-traffic use.
- **Email**: Requires SMTP configuration (consider SendGrid/AWS SES for production).

## Acknowledgments

Special thanks to:
- **CS50 Staff** for the excellent course and CS50 SQL library
- **CurrencyLayer** for the currency conversion API
- **Google** for OAuth 2.0 infrastructure
- **Flask, Bootstrap, ReportLab, pytest** communities for excellent tools and documentation

## License

This project is submitted as part of Harvard's CS50 course. Please respect academic integrity policies.

---

## Summary

FinTrack demonstrates a production-ready personal finance platform emphasizing:

✅ **Multi-Currency Transactions** with CurrencyLayer API integration
✅ **Advanced Security** with OAuth 2.0, CSRF protection, rate limiting, and audit logging
✅ **Data Export** capabilities with CSV and PDF generation using ReportLab
✅ **Clean Architecture** with service layer separation and comprehensive testing
✅ **Modern Stack** with Flask, SQLite, and 70+ automated test cases

Built as a CS50 final project showcasing full-stack web development, database design, API integration, security implementation, and software engineering best practices.
