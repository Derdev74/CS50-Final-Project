import requests
from flask import redirect, render_template, session, flash
from functools import wraps
from datetime import datetime
from cs50 import SQL

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.
        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First check: Is user logged in at all?
        if session.get("user_id") is None:
            return redirect("/login")
        
        # User is logged in, now check timeout
        if 'login_time' in session:
            login_time = datetime.fromisoformat(session['login_time'])
            if datetime.now() - login_time > app.config['PERMANENT_SESSION_LIFETIME']:
                session.clear()
                flash('Your session has expired. Please log in again.', 'info')
                return redirect("/login")
        
        # Validate user still exists
        user = db.execute("SELECT id FROM users WHERE id = ?", session['user_id'])
        if not user:
            session.clear()
            return redirect("/login")
        
        # Check IP address
        if 'ip_address' in session and session['ip_address'] != request.remote_addr:
            session.clear()
            flash('Session security check failed. Please log in again.', 'warning')
            return redirect("/login")
        
        return f(*args, **kwargs)
    
    return decorated_function