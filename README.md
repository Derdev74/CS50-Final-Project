# FinTrack
#### Video Demo: https://youtu.be/REPLACE_WITH_YOUR_VIDEO_ID
#### Description:

FinTrack is a lightweight personal finance and budgeting web application built for my CS50 final project. It enables a registered user to record income and expenses, organize them into categories, set and track saving goals, define budgets, perform filtered data exports (CSV, plus a PDF stub), and observe basic security protections (authentication, rate limiting, session timeout, injection and rudimentary XSS defense). The project emphasizes correctness, clarity, testability, and incremental hardening rather than flashy UI. Nearly all interactive logic is covered by an automated pytest suite spanning authentication, budgets, categories, goals, transactions, exports, integration workflows, and security scenarios.

## Core Features

1. User Authentication  
   - Registration with duplicate detection and password complexity evaluation.  
   - Login with account lockout on repeated failures and simple login rate limiting.  
   - Session timeout enforcement: stale sessions (over a configured threshold) force re‑authentication.  
2. Transactions  
   - Create income or expense entries (amount automatically negated for expense categories).  
   - Filtering by category and date range, and pagination for lists.  
   - Editing and deletion adjust the user’s running cash balance.  
   - Support for multi‑currency fields (original amount and exchange rate) with a normalized base amount (simplified logic in this version).  
3. Categories  
   - System categories plus user‑defined custom categories (with type: income or expense).  
   - Editing and soft constraints to avoid accidental duplication.  
4. Budgets  
   - Per-category budget definitions with period (monthly, weekly, annual etc.).  
   - Prevention of exact duplicate active budget records.  
   - Consumption/spending calculations inferred from related transactions.  
5. Goals  
   - Savings goals with target, current progress, and deadline.  
   - Unified route for adding progress or withdrawing funds.  
   - Emits a clear completion message: “Congratulations! Goal completed”.  
6. Data Export  
   - CSV endpoints for transactions, budgets, and goals with consistent headers (Transaction ID, Budget ID, Goal ID).  
   - Transaction exports support filtering (date range + category).  
   - A PDF “complete report” endpoint returns a binary stub illustrating the future extension point.  
   - Export rate limiting with per‑user attempt tracking; tests reset counters to avoid cross‑test interference.  
7. Security Enhancements  
   - Parameterized database queries to mitigate SQL injection.  
   - Minimal XSS mitigation by avoiding raw reflection of untrusted input in responses used by tests.  
   - Account lockout & login attempt tracking.  
   - Security event logging stored centrally in a `security_logs` table.  
   - Basic password policy: length, uppercase, lowercase, digit, special character.  
8. Testing & Quality  
   - Dozens of pytest cases across distinct modules (auth, goals, budgets, categories, transactions, export, integration, security).  
   - Fixtures seed deterministic data (users, categories, transactions, budgets, goals).  
   - Autouse fixtures reset mutable global state (e.g. export rate limit counters) to ensure isolation.  

## File Overview

- `app.py`  
  The central Flask application module containing route handlers for authentication, transactions, categories, budgets, goals, and export endpoints. Implements session validation, input parsing, cash balance updates, goal progress logic, withdrawal handling, and simple plain‑text responses that facilitate assertion in tests. Also includes rate limiting logic for exports and security event logging calls.

- `export_service.py`  
  Encapsulates CSV generation for transactions, budgets, and goals plus a PDF stub method. Provides a thin separation of concerns so route handlers stay focused on HTTP/context logic while formatting lives in a dedicated service.

- `conftest.py`  
  Pytest configuration and fixtures. Seeds a test user, categories, sample transactions, a budget, and a “Test Savings” goal. Supplies authenticated client fixtures, resets export rate limits, and inserts deterministic data enabling integration and security tests to run consistently. An autouse fixture ensures the presence of a baseline goal the workflow tests expect to find before creation.

- `templates/` (e.g. `transactions.html`, `goals.html`, etc.)  
  Minimal placeholders extending a base layout. For the testing focus of this project, templates are intentionally sparse. They can be expanded later with richer UI, CSRF tokens, and front‑end enhancements.

- `tests/`  
  Organized test modules:
  - `test_auth.py`: Registration, login, logout, lockout, session persistence.
  - `test_transactions.py`: CRUD operations, filtering, pagination, currency conversion.
  - `test_budgets.py`: Create/edit/delete budgets, spending math, duplicate prevention.
  - `test_categories.py`: User category CRUD and duplicate handling.
  - `test_goals.py`: Goal creation, progress updates, withdrawals, completion path.
  - `test_export.py`: CSV content validation, filters, rate limiting, PDF stub.
  - `test_integration.py`: Multi‑step workflows covering combined features (budget flow, goal tracking, multi‑currency, full export).
  - `test_security.py`: SQL injection resistance, XSS attempt, CSRF stance (lenient or blocked), unauthorized resource access, password complexity, session timeout, login rate limiting.
  - `test_hello.py`: Simple baseline sanity checks.
  
- `README.md`  
  This documentation file.

(If a schema/migration script or requirements file exists externally, it should be referenced here; for brevity they are omitted in this summary.)

## Design Decisions & Trade‑Offs

1. Plain‑Text Responses for Tests  
   Returning simple body strings (e.g. “Invalid amount”, “Withdrawal successful”) makes assertions deterministic and avoids coupling tests to HTML layout that could change.

2. Lightweight Data Layer  
   Direct parameterized SQL via a provided `db.execute` wrapper keeps the stack lean (no heavy ORM) and surfaces SQL clearly—beneficial for learning and auditing.

3. Centralized Export Service  
   Extracting CSV generation reduces duplication, ensures consistent headers, and eases future replacement of the PDF stub with a real reporting engine.

4. Explicit Goal Progress Logic  
   One unified update route with an action parameter (add/withdraw) simplified branching and kept completion detection stable.

5. Test Isolation via Fixtures  
   The `_reset_export_rate_limit` fixture ensures rate limiting does not create flaky inter‑test dependencies—critical for reliability.

6. Security Logging  
   Logging each sensitive change (add/edit/delete transaction, goal updates, exports) supports traceability and would help in real auditing scenarios, even though formatting is minimal here.

7. Minimal Templates  
   UI complexity was intentionally deprioritized in favor of backend correctness and breadth of functional coverage. This leaves clear extension points without retrofitting large refactors.

## Future Enhancements

- Replace PDF stub with a real rendering engine (ReportLab / WeasyPrint).
- Add proper CSRF tokens using Flask‑WTF across all modifying forms.
- Integrate a currency conversion API and historical rate caching.
- Provide richer analytics dashboards and category/goal visualizations.
- Implement full role-based permissions (e.g., shared budgets).
- Add comprehensive audit export and downloadable logs.
- Introduce pagination + sorting parameters to budget and goal listings.

## How to Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=app.py
flask run
```

Run tests:

```bash
pytest -v
```

## Conclusion

FinTrack demonstrates an end‑to‑end personal finance platform with robust functional coverage, pragmatic security measures, and an extensive automated test suite. The design choices favor transparency, testability, and incremental hardening—forming a solid base for future UI polish and advanced reporting features.