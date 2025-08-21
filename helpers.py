
# Import necessary Flask objects
from flask import redirect, render_template, session, flash, request, current_app, g
from functools import wraps
from datetime import datetime


def apology(message, code=400):
    """
    Render message as an apology to user.
    Args:
        message (str): The message to display.
        code (int): HTTP status code to return.
    Returns:
        Rendered apology template and status code.
    """
    def escape(s):
        """
        Escape special characters for meme generator compatibility.
        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    # Pass 'top' and 'bottom' to apology.html for error display
    return render_template("apology.html", top=code, bottom=escape(message)), code
def login_required(f):
    """
    Decorator to require login for a route. Checks session, timeout, user existence, and IP address.
    Uses Flask's current_app and g for config and db access.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in
        if session.get("user_id") is None:
            return redirect("/login")

        # Check session timeout using app config
        if 'login_time' in session:
            login_time = datetime.fromisoformat(session['login_time'])
            if datetime.now() - login_time > current_app.config['PERMANENT_SESSION_LIFETIME']:
                session.clear()
                flash('Your session has expired. Please log in again.', 'info')
                return redirect("/login")

        # Get db from Flask's g (global context) or fallback to current_app
        db = getattr(g, 'db', None)
        if db is None:
            db = current_app.config.get('db')
        # Validate user still exists in database
        if db:
            user = db.execute("SELECT id FROM users WHERE id = ?", session['user_id'])
            if not user:
                session.clear()
                return redirect("/login")

        # Check IP address for session security
        if 'ip_address' in session and session['ip_address'] != request.remote_addr:
            session.clear()
            flash('Session security check failed. Please log in again.', 'warning')
            return redirect("/login")

        return f(*args, **kwargs)
    return decorated_function