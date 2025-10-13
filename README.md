# FinTrack
#### Video Demo: https://youtu.be/V3Sh8TzrqR0
#### Description:

FinTrack is a comprehensive personal finance and budgeting web application built for my CS50 final project. It enables users to track income and expenses, organize transactions into categories, set and monitor saving goals, define budgets, manage multiple currencies, and export data in various formats. The application features robust security measures including OAuth authentication (Google Sign-In), email verification, password reset functionality, rate limiting, session management, and comprehensive audit logging. Built with Flask and SQLite, the project emphasizes production-ready code quality, security best practices, testability, and user experience through a clean, responsive interface.

## Core Features

### 1. User Authentication & Security
- **Registration**: Comprehensive user registration with duplicate detection, email verification, and strong password complexity requirements (minimum 8 characters, uppercase, lowercase, digit, special character)
- **Login System**: Secure login with Flask-WTF form validation, account lockout after 10 failed attempts (30-minute lockout), and rate limiting
- **Google OAuth**: Alternative sign-in via Google OAuth 2.0 with secure token exchange and user info retrieval
- **Password Reset**: Email-based password reset with secure token generation and expiration (15-minute timeout)
- **Session Management**: 24-hour session lifetime with timeout enforcement, IP address verification, and secure session storage
- **Email Verification**: Token-based email verification system with attempt tracking and rate limiting

### 2. Transaction Management
- **Create Transactions**: Record income and expense entries with automatic amount negation for expense categories
- **Multi-Currency Support**: Track transactions in multiple currencies with real-time exchange rate conversion via CurrencyLayer API
- **Currency Service**: Intelligent caching system for exchange rates (1-hour cache duration) with fallback to static rates
- **Filtering & Search**: Filter transactions by category, date range, and transaction type
- **Pagination**: Efficient pagination for large transaction lists
- **CRUD Operations**: Full create, read, update, and delete functionality with automatic cash balance adjustments
- **Detailed Transaction View**: View and edit individual transactions with description, amount, category, currency, and exchange rate

### 3. Categories
- **System Categories**: 15 pre-defined categories including Food & Dining, Transportation, Shopping, Entertainment, Bills & Utilities, Healthcare, Education, Salary, Freelance, Investments, and more
- **User Categories**: Create custom categories with type classification (income or expense), custom icons, and color coding
- **Category Management**: Edit, activate/deactivate, and organize categories with duplicate prevention
- **Visual Indicators**: Icon and color support for better category recognition

### 4. Budget Management
- **Budget Creation**: Set budgets per category with flexible time periods (weekly, monthly, yearly)
- **Budget Tracking**: Real-time spending calculations showing budget consumption vs. target amount
- **Duplicate Prevention**: System prevents creation of duplicate active budget records
- **Budget Overview**: Dashboard view of all active budgets with progress indicators
- **Budget Analytics**: Visual representation of budget utilization

### 5. Goals & Savings
- **Savings Goals**: Create savings goals with target amount, deadline, and current progress tracking
- **Goal Types**: Support for various goal types (savings, investment, debt repayment, etc.)
- **Progress Management**: Add progress or withdraw funds from goals with unified update route
- **Goal Completion**: Automatic completion detection with congratulatory messaging
- **Recurring Goals**: Support for recurring savings goals
- **Visual Tracking**: Color-coded progress bars and percentage completion indicators
- **Notes & Details**: Attach notes and additional details to goals

### 6. Data Export & Reporting
- **CSV Export**: Export transactions, budgets, and goals with consistent, structured headers
  - Transaction exports include: Transaction ID, Category, Amount, Currency, Date, Description
  - Budget exports include: Budget ID, Category, Amount, Period, Start Date, Spending
  - Goal exports include: Goal ID, Name, Target Amount, Current Amount, Progress %, Deadline
- **Filtered Exports**: Transaction exports support filtering by date range and category
- **PDF Reports**: PDF generation capability using ReportLab and WeasyPrint for comprehensive financial reports
- **Rate Limiting**: Export rate limiting (10 exports per hour) to prevent abuse
- **Download Management**: Secure file generation with proper MIME types and headers

### 7. Dashboard & Analytics
- **Financial Overview**: Real-time cash balance display with starting balance tracking
- **Quick Stats**: Summary cards showing total income, expenses, budget status, and goal progress
- **Recent Activity**: Display of recent transactions and upcoming goal deadlines
- **Visual Charts**: Budget consumption charts and spending trends
- **Responsive Design**: Mobile-friendly dashboard with clean, intuitive interface

### 8. Security Features
- **SQL Injection Protection**: Parameterized queries throughout the application using CS50's SQL library
- **XSS Prevention**: Input sanitization and proper escaping of user-generated content
- **CSRF Protection**: Flask-WTF CSRF token implementation on all forms
- **Password Hashing**: Werkzeug security for bcrypt password hashing
- **Security Logging**: Comprehensive audit trail in `security_logs` table tracking:
  - Login/logout events
  - Failed login attempts
  - Password resets
  - Transaction modifications
  - Goal updates
  - Data exports
  - IP addresses and user agents
- **Rate Limiting**: Multiple rate limiting layers:
  - Login attempts (5 attempts per 5 minutes)
  - Export requests (10 per hour)
  - Email verification attempts
  - Password reset requests
- **Account Protection**: Automatic account lockout, session timeout, and IP validation

### 9. User Profile & Preferences
- **Profile Management**: Update username, email, and personal information
- **Theme Selection**: Light/dark theme toggle for user interface
- **Currency Preference**: Set preferred currency for displaying amounts (40+ currencies supported)
- **Profile Statistics**: View account creation date, last login, and account activity summary

### 10. Testing & Quality Assurance
- **Comprehensive Test Suite**: Extensive pytest coverage with 70+ test cases across 8 test modules:
  - `test_auth.py`: Registration, login, logout, lockout, OAuth flow, session persistence
  - `test_transactions.py`: CRUD operations, filtering, pagination, currency conversion
  - `test_budgets.py`: Create/edit/delete budgets, spending calculations, duplicate prevention
  - `test_categories.py`: User category CRUD, duplicate handling, system categories
  - `test_goals.py`: Goal creation, progress updates, withdrawals, completion scenarios
  - `test_export.py`: CSV content validation, filters, rate limiting, PDF generation
  - `test_integration.py`: Multi-step workflows, end-to-end scenarios, complex user journeys
  - `test_security.py`: SQL injection resistance, XSS attempts, CSRF validation, unauthorized access, password complexity, session timeout
- **Test Fixtures**: Deterministic test data seeding with automatic cleanup
- **Isolation**: Autouse fixtures for state reset (export counters, rate limits)
- **Coverage**: pytest-cov integration for code coverage reporting

## Project Structure

### Core Application Files

- **`app.py`** (3,700+ lines)
  The main Flask application containing all route handlers, database initialization, form definitions, and business logic. Implements:
  - User authentication routes (register, login, logout, password reset, email verification)
  - Transaction management (create, read, update, delete)
  - Budget and goal CRUD operations
  - Category management
  - Data export endpoints
  - OAuth callback handlers
  - Dashboard and profile views
  - Database schema creation with 9 tables
  - Rate limiting and security logging

- **`helpers.py`** (420 lines)
  Helper functions and decorators including:
  - `CurrencyService`: Comprehensive currency conversion service with API integration, caching, and 40+ supported currencies
  - `login_required`: Decorator for route protection with session validation, timeout checking, IP verification
  - `with_currency_conversion`: Decorator for automatic currency service injection
  - `apology`: Error page rendering with custom messages

- **`services.py`** (148 lines)
  Service layer classes for clean separation of concerns:
  - `UserService`: User data operations (lookup, creation, password updates, account locking)
  - `AuthService`: Authentication logic, password validation (8+ characters, complexity rules), login flow, lockout management

- **`export_service.py`** (645 lines)
  Dedicated export functionality:
  - CSV generation for transactions, budgets, and goals
  - PDF report generation using ReportLab and WeasyPrint
  - Consistent header formatting and data structure
  - Support for filtered exports
  - Pandas integration for data manipulation

- **`oauth_service.py`** (209 lines)
  Google OAuth 2.0 integration:
  - `GoogleOAuthService`: Handles OAuth flow, token exchange, user info retrieval
  - Provider configuration with OpenID Connect discovery
  - Authorization URL generation with CSRF protection
  - ID token verification and validation
  - Secure token storage and management

- **`conftest.py`** (410 lines)
  Pytest configuration and fixtures:
  - Test database setup and teardown
  - User authentication fixtures
  - Sample data seeding (users, categories, transactions, budgets, goals)
  - Rate limit reset fixtures
  - Flask test client configuration
  - Isolation utilities

### Templates

The `templates/` directory contains 18 HTML templates:

- **Authentication**: `login.html`, `register.html`, `forgot_password.html`, `reset_password.html`
- **Main Views**: `dashboard.html`, `transactions.html`, `budget.html`, `goals.html`, `categories.html`, `profile.html`
- **Transactions**: `edit_transaction.html`
- **Emails**: `emails/email_verification.html`, `emails/password_reset.html`
- **Error Pages**: `404.html`, `500.html`, `apology.html`, `rate_limit.html`
- **Base Layout**: `layout.html` with responsive navigation and flash messaging

### Static Assets

- **`static/css/`**: Custom stylesheets for theming and responsive design
- **`static/js/`**: JavaScript for interactive features and form validation

### Test Suite

The `tests/` directory contains comprehensive test coverage:

- `test_hello.py`: Basic sanity checks
- `test_auth.py`: Authentication flows and security
- `test_transactions.py`: Transaction management
- `test_budgets.py`: Budget tracking
- `test_categories.py`: Category management
- `test_goals.py`: Goal tracking and completion
- `test_export.py`: Data export functionality
- `test_integration.py`: End-to-end workflows
- `test_security.py`: Security validation

### Configuration Files

- **`requirements.txt`**: Production dependencies (Flask, CS50, Pandas, ReportLab, WeasyPrint, Authlib, Flask-WTF, Flask-Mail, Flask-Limiter, Google Auth, etc.)
- **`requirements-test.txt`**: Testing dependencies (pytest, pytest-flask, pytest-cov, pytest-mock, faker)
- **`pytest.ini`**: Pytest configuration
- **`.env`**: Environment variables (SECRET_KEY, mail server config, OAuth credentials, API keys)
- **`.gitignore`**: Git ignore rules

### Database

- **`instance/fintrack.db`**: SQLite database with 9 tables:
  - `users`: User accounts with authentication and preferences
  - `categories`: System-wide category definitions
  - `user_categories`: User-created custom categories
  - `transactions`: Financial transaction records with multi-currency support
  - `budgets`: Budget definitions with period tracking
  - `goals`: Savings goals with progress tracking
  - `security_logs`: Comprehensive audit trail
  - `email_verification_attempts`: Email verification rate limiting
  - `exchange_rates`: Currency conversion rate cache

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token TEXT,
    email_verification_expires TIMESTAMP,
    password_reset_token TEXT,
    password_reset_expires TIMESTAMP,
    google_id TEXT,
    oauth_provider TEXT,
    cash NUMERIC NOT NULL DEFAULT 10000.00,
    theme TEXT DEFAULT 'light',
    preferred_currency TEXT DEFAULT 'USD',
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP NULL,
    last_login TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Transactions Table
```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category_id INTEGER,
    amount NUMERIC NOT NULL,
    original_amount NUMERIC,
    currency TEXT DEFAULT 'USD',
    exchange_rate NUMERIC DEFAULT 1.0,
    description TEXT,
    date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
);
```

### Goals Table
```sql
CREATE TABLE goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    target_amount NUMERIC NOT NULL,
    current_amount NUMERIC DEFAULT 0,
    deadline DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    goal_type TEXT DEFAULT 'savings',
    notes TEXT,
    color TEXT DEFAULT '#4CAF50',
    is_recurring BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

Additional tables: `categories`, `user_categories`, `budgets`, `security_logs`, `email_verification_attempts`, `exchange_rates`

Performance indexes on user_id, date, category_id, email, and username columns.

## Design Decisions & Architecture

### 1. Service Layer Architecture
Separation of concerns with dedicated service classes (`UserService`, `AuthService`, `CurrencyService`, `ExportService`, `GoogleOAuthService`) keeps route handlers clean and business logic testable.

### 2. CS50 SQL Library
Direct parameterized SQL using CS50's `SQL` wrapper provides:
- Clear visibility into database operations
- Protection against SQL injection
- Simplicity without ORM overhead
- Educational value for learning SQL

### 3. Currency Service with Caching
The `CurrencyService` implements intelligent caching:
- API calls to CurrencyLayer for real-time rates
- 1-hour cache duration to minimize API costs
- Fallback to static rates when API unavailable
- Support for 40+ currencies
- Cross-rate calculations through USD

### 4. Security-First Design
Multiple security layers:
- Parameterized queries prevent SQL injection
- Werkzeug password hashing with bcrypt
- Flask-WTF CSRF protection
- Input validation and sanitization
- Rate limiting on sensitive operations
- Comprehensive audit logging
- Session security with IP validation and timeout

### 5. OAuth Integration
Google OAuth provides:
- Passwordless authentication option
- Reduced friction for new users
- Secure token exchange
- ID token verification
- State parameter for CSRF protection

### 6. Export Service Abstraction
Centralized export logic:
- Consistent CSV headers across all exports
- Pandas integration for data manipulation
- PDF generation with ReportLab
- Rate limiting to prevent abuse
- Filtered export support

### 7. Comprehensive Testing
Test-driven approach:
- 70+ test cases with pytest
- Fixtures for deterministic data
- Autouse fixtures for state isolation
- Integration tests for complex workflows
- Security-specific test suite
- Code coverage tracking

### 8. Responsive UI Templates
Templates built with:
- Bootstrap for responsive design
- Jinja2 templating with inheritance
- Flash message system for user feedback
- Error handling pages (404, 500, rate limit)
- Mobile-first approach

### 9. Environment-Based Configuration
Flexible configuration:
- `.env` file for sensitive credentials
- Different database paths for dev/production
- Configurable timeouts and limits
- Feature flags (registration, password reset)

### 10. Scalability Considerations
While using SQLite for simplicity:
- Indexed columns for query performance
- Pagination for large datasets
- Efficient filtering with SQL WHERE clauses
- Connection pooling via CS50 SQL
- Ready migration path to PostgreSQL/MySQL

## Technology Stack

### Backend
- **Flask 2.3.3**: Web framework
- **CS50 9.2.5**: Database library wrapper
- **SQLite**: Database engine
- **Werkzeug 2.3.7**: Security utilities (password hashing)
- **Python 3.12**: Programming language

### Authentication & Security
- **Flask-Login 0.6.3**: User session management
- **Flask-WTF 1.1.1**: Form validation and CSRF protection
- **WTForms 3.0.1**: Form rendering and validation
- **Authlib 1.2.1**: OAuth client library
- **Google Auth 2.23.4**: Google OAuth integration
- **Flask-Limiter 3.5.0**: Rate limiting

### Data Processing & Export
- **Pandas 2.1.1**: Data manipulation
- **ReportLab 4.0.7**: PDF generation
- **WeasyPrint 60.1**: Advanced PDF rendering

### Email & Notifications
- **Flask-Mail 0.9.1**: Email sending
- **Python email.mime**: Email formatting

### Session Management
- **Flask-Session 0.5.0**: Server-side session storage

### Development & Testing
- **pytest 7.4.3**: Testing framework
- **pytest-flask 1.3.0**: Flask testing utilities
- **pytest-cov 4.1.0**: Code coverage
- **pytest-mock 3.12.0**: Mocking utilities
- **faker 20.1.0**: Test data generation

### Additional Libraries
- **python-dotenv 1.0.0**: Environment variable management
- **python-dateutil 2.8.2**: Date manipulation
- **requests 2.31.0**: HTTP client

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment tool (venv)

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd "Final project"
```

### Step 2: Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-test.txt  # For testing
```

### Step 4: Configure Environment Variables
Create a `.env` file in the project root:

```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_APP=app.py
FLASK_ENV=development

# Mail Server Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Currency API (Optional)
CURRENCYLAYER_API_KEY=your-api-key
```

### Step 5: Initialize Database
The database will be automatically initialized on first run. The application creates:
- All necessary tables
- Default categories
- Required indexes

### Step 6: Run the Application
```bash
flask run
```

The application will be available at `http://127.0.0.1:5000`

### Step 7: Run Tests
```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=app --cov=services --cov=helpers --cov=export_service --cov=oauth_service

# Run specific test file
pytest tests/test_auth.py -v
```

### Step 8: Run Tests Script
```bash
chmod +x run_tests.sh
./run_tests.sh
```

## Usage Guide

### 1. Registration
- Navigate to `/register`
- Fill in username (3-50 characters, alphanumeric with dots, hyphens, underscores)
- Provide valid email address
- Create strong password (8+ characters, uppercase, lowercase, digit, special character)
- Accept terms of service
- Verify email (check inbox for verification link)

### 2. Login
- Navigate to `/login`
- Enter username and password
- Or click "Sign in with Google" for OAuth login
- Optional: Check "Remember Me" for extended session

### 3. Dashboard
After login, view your financial overview:
- Current cash balance
- Quick stats (income, expenses, budget status)
- Recent transactions
- Upcoming goal deadlines
- Budget consumption charts

### 4. Transactions
- Click "Transactions" in navigation
- Add new transaction with amount, category, description, date
- Select currency if not using default
- View, edit, or delete existing transactions
- Filter by category or date range
- Paginate through transaction history

### 5. Categories
- Navigate to "Categories"
- View system categories (15 pre-defined)
- Create custom categories with icon and color
- Edit or deactivate categories as needed
- Categories automatically organize transactions

### 6. Budgets
- Click "Budgets" to manage budgets
- Create budget by selecting category, amount, and period
- View real-time spending vs. budget
- Edit or delete budgets
- Visual progress bars show consumption

### 7. Goals
- Navigate to "Goals"
- Create savings goal with name, target amount, and deadline
- Add progress by contributing funds
- Withdraw funds when needed
- View percentage completion
- Receive congratulations on goal completion
- Add notes and customize colors

### 8. Profile
- Click username in navigation
- Update personal information
- Change theme (light/dark)
- Set preferred currency
- View account statistics
- Change password

### 9. Export Data
- From dashboard or individual pages
- Export transactions to CSV (with optional filters)
- Export budgets to CSV
- Export goals to CSV
- Generate PDF reports (comprehensive financial summary)
- Rate limited to 10 exports per hour

### 10. Password Reset
- Click "Forgot Password?" on login page
- Enter email address
- Check email for reset link (15-minute expiration)
- Create new password
- Redirected to login

## Security Best Practices Implemented

1. **Authentication**
   - Strong password requirements enforced
   - Account lockout after 10 failed attempts
   - Session timeout after 24 hours
   - IP address validation for sessions

2. **Data Protection**
   - All passwords hashed with Werkzeug (bcrypt)
   - Parameterized SQL queries prevent injection
   - CSRF tokens on all forms
   - XSS protection through proper escaping

3. **Rate Limiting**
   - Login attempts: 5 per 5 minutes
   - Export requests: 10 per hour
   - Email verification: tracked and limited
   - Password reset: 15-minute token expiration

4. **Audit Trail**
   - All security events logged with timestamps
   - IP addresses and user agents recorded
   - Transaction modifications tracked
   - Failed login attempts monitored

5. **OAuth Security**
   - State parameter for CSRF protection
   - ID token verification
   - Secure token exchange
   - HTTPS for all OAuth communications (production)

## Future Enhancements

### Near-Term Improvements
- [ ] Enhanced PDF reports with charts and visualizations
- [ ] Email notifications for budget limits and goal milestones
- [ ] Recurring transactions and automated budgets
- [ ] Bank account integration (Plaid API)
- [ ] Mobile app (React Native)
- [ ] Advanced analytics and spending insights

### Medium-Term Goals
- [ ] Shared budgets for families/roommates
- [ ] Bill reminders and payment tracking
- [ ] Investment portfolio tracking
- [ ] Tax preparation export (1099, W-2 compatible)
- [ ] Multi-user permissions and roles
- [ ] API for third-party integrations

### Long-Term Vision
- [ ] Machine learning for spending predictions
- [ ] AI-powered financial advice
- [ ] Cryptocurrency wallet integration
- [ ] International banking support
- [ ] Financial goal recommendations
- [ ] Social features (spending challenges, leaderboards)

### Technical Improvements
- [ ] Migration to PostgreSQL for scalability
- [ ] Redis caching layer
- [ ] Celery for background tasks (email, exports)
- [ ] WebSocket for real-time updates
- [ ] Kubernetes deployment configuration
- [ ] CI/CD pipeline with GitHub Actions
- [ ] Comprehensive API documentation
- [ ] GraphQL API endpoint

## Known Limitations

1. **SQLite Database**: Suitable for single-user or small-scale deployment. Production use should migrate to PostgreSQL or MySQL.

2. **Email Service**: Currently requires SMTP configuration. Future versions could use SendGrid or AWS SES.

3. **Currency API**: Free tier of CurrencyLayer has rate limits. Upgrade for production use.

4. **Session Storage**: File-based sessions are not suitable for distributed deployments. Use Redis in production.

5. **OAuth Providers**: Currently only Google. Future versions could add GitHub, Facebook, Apple.

6. **PDF Generation**: WeasyPrint requires system dependencies. Consider cloud-based PDF generation for deployment simplicity.

## Troubleshooting

### Database Issues
```bash
# Reset database
rm instance/fintrack.db
flask run  # Will reinitialize
```

### Dependency Errors
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### OAuth Not Working
- Check `.env` file has correct Google credentials
- Verify redirect URI matches Google Console configuration
- Ensure `OAUTHLIB_INSECURE_TRANSPORT=1` for local development

### Email Not Sending
- Verify SMTP credentials in `.env`
- For Gmail, use App Password (not regular password)
- Check firewall allows SMTP traffic (port 587)

### Tests Failing
```bash
# Clear pytest cache
pytest --cache-clear

# Run with verbose output
pytest -vv --tb=long
```

## Contributing

This project was created as a CS50 final project. While it's primarily an educational project, suggestions and improvements are welcome:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Commit changes (`git commit -m 'Add improvement'`)
4. Push to branch (`git push origin feature/improvement`)
5. Open a Pull Request

## License

This project is submitted as part of Harvard's CS50 course. Please respect academic integrity policies.

## Acknowledgments

- **CS50 Staff**: For providing an excellent course and the CS50 SQL library
- **Flask Community**: For comprehensive documentation and examples
- **Google OAuth**: For secure authentication infrastructure
- **CurrencyLayer**: For currency conversion API
- **Bootstrap**: For responsive UI components
- **Pytest**: For robust testing framework

## Author

Created as a CS50 Final Project - demonstrating full-stack web development, database design, security implementation, testing, and software engineering best practices.

## Conclusion

FinTrack demonstrates a production-ready personal finance platform with:
- **Comprehensive Features**: Transaction tracking, budgets, goals, multi-currency, exports
- **Security-First Design**: Authentication, authorization, audit logging, rate limiting, CSRF protection
- **Clean Architecture**: Service layer, separation of concerns, testable code
- **Extensive Testing**: 70+ test cases, integration tests, security validation
- **Modern Stack**: Flask, SQLite, OAuth, RESTful design, responsive UI
- **Best Practices**: PEP 8 compliance, documentation, error handling, logging

The project serves as a solid foundation for a real-world financial application and demonstrates the skills learned throughout CS50, including Python programming, web development, database design, security implementation, and software testing.
