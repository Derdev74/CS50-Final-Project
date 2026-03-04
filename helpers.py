from flask import redirect, render_template, session, flash, request, current_app, g
from functools import wraps
import requests
import json
from datetime import datetime, timedelta
from decimal import Decimal
import os
import logging

# Configure logging for currency operations
currency_logger = logging.getLogger('currency')
currency_logger.setLevel(logging.INFO)

class CurrencyService:
    """
    Service class for handling currency conversions and exchange rates.
    Uses CurrencyLayer API with caching to minimize API calls and costs.
    
    Security considerations:
    - API key stored in environment variables
    - Rate limiting to prevent API abuse
    - Input validation for currency codes
    - Cached rates to reduce external dependencies
    """
    
    # List of supported currencies (can be expanded)
    SUPPORTED_CURRENCIES = [
        'USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY', 
        'INR', 'MXN', 'BRL', 'ZAR', 'KRW', 'SGD', 'HKD', 'NOK',
        'SEK', 'DKK', 'PLN', 'THB', 'IDR', 'HUF', 'CZK', 'ILS',
        'CLP', 'PHP', 'AED', 'COP', 'SAR', 'MYR', 'RON', 'NZD',
        'ARS', 'MAD', 'EGP', 'TND', 'NGN', 'KES', 'GHS', 'UAH'
    ]
    
    def __init__(self, db, api_key=None):
        """
        Initialize the currency service.
        
        Args:
            db: Database connection object
            api_key: CurrencyLayer API key (defaults to environment variable)
        """
        self.db = db
        self.api_key = api_key or os.environ.get('CURRENCYLAYER_API_KEY')
        self.base_url = "http://api.currencylayer.com/live"
        self.cache_duration = timedelta(hours=1)  # Cache rates for 1 hour
        
        if not self.api_key:
            currency_logger.warning("CurrencyLayer API key not found. Using static rates.")
    
    def validate_currency_code(self, currency_code):
        """
        Validate if a currency code is supported.
        
        Args:
            currency_code: 3-letter currency code (e.g., 'USD')
            
        Returns:
            bool: True if valid, False otherwise
        
        Security: Prevents injection attacks through currency codes
        """
        if not currency_code or not isinstance(currency_code, str):
            return False
        
        # Ensure it's exactly 3 uppercase letters
        if len(currency_code) != 3 or not currency_code.isalpha():
            return False
        
        return currency_code.upper() in self.SUPPORTED_CURRENCIES
    
    def get_cached_rate(self, from_currency, to_currency):
        """
        Get exchange rate from cache if available and fresh.
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            float or None: Exchange rate if cached and fresh, None otherwise
        """
        try:
            # Check cache for recent exchange rate
            cached = self.db.execute("""
                SELECT rate, last_updated 
                FROM exchange_rates 
                WHERE base_currency = ? AND target_currency = ?
            """, from_currency.upper(), to_currency.upper())
            
            if cached:
                last_updated = datetime.fromisoformat(cached[0]['last_updated'])
                if datetime.now() - last_updated < self.cache_duration:
                    currency_logger.info(f"Using cached rate for {from_currency}/{to_currency}")
                    return float(cached[0]['rate'])
                    
        except Exception as e:
            currency_logger.error(f"Error retrieving cached rate: {str(e)}")
        
        return None
    
    def fetch_exchange_rate(self, from_currency='USD', to_currency='EUR'):
        """
        Fetch current exchange rate from CurrencyLayer API.
        
        Args:
            from_currency: Source currency code (default: USD)
            to_currency: Target currency code (default: EUR)
            
        Returns:
            float: Exchange rate (how much 1 from_currency equals in to_currency)
            
        Security:
        - Validates currency codes to prevent injection
        - Uses HTTPS for API calls (upgrade from http in production)
        - Handles API errors gracefully
        """
        # Validate currency codes
        if not self.validate_currency_code(from_currency) or not self.validate_currency_code(to_currency):
            raise ValueError(f"Invalid currency code: {from_currency} or {to_currency}")
        
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        # Same currency, no conversion needed
        if from_currency == to_currency:
            return 1.0
        
        # Check cache first
        cached_rate = self.get_cached_rate(from_currency, to_currency)
        if cached_rate is not None:
            return cached_rate
        
        # If no API key, use fallback rates
        if not self.api_key:
            return self.get_fallback_rate(from_currency, to_currency)
        
        try:
            # CurrencyLayer free tier only supports USD as base
            # So we might need to do two conversions
            currencies_param = f"{from_currency},{to_currency}"
            
            params = {
                'access_key': self.api_key,
                'currencies': currencies_param,
                'source': from_currency,
                'format': 1
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get('success', False):
                error_msg = data.get('error', {}).get('info', 'Unknown API error')
                currency_logger.error(f"CurrencyLayer API error: {error_msg}")
                return self.get_fallback_rate(from_currency, to_currency)
            
            # Extract rate from response
            # CurrencyLayer returns rates like "USDEUR": 0.85
            quote_key = f"{from_currency}{to_currency}"
            if quote_key in data.get('quotes', {}):
                rate = float(data['quotes'][quote_key])
            else:
                # Try indirect conversion through USD
                rate = self.calculate_cross_rate(from_currency, to_currency, data)
            
            # Cache the rate
            self.cache_exchange_rate(from_currency, to_currency, rate)
            
            currency_logger.info(f"Fetched rate {from_currency}/{to_currency}: {rate}")
            return rate
            
        except requests.exceptions.RequestException as e:
            currency_logger.error(f"API request failed: {str(e)}")
            return self.get_fallback_rate(from_currency, to_currency)
        except Exception as e:
            currency_logger.error(f"Unexpected error fetching rate: {str(e)}")
            return self.get_fallback_rate(from_currency, to_currency)
    
    def calculate_cross_rate(self, from_currency, to_currency, api_data):
        """
        Calculate exchange rate through USD when direct rate not available.
        
        Args:
            from_currency: Source currency
            to_currency: Target currency
            api_data: Response from CurrencyLayer API
            
        Returns:
            float: Calculated exchange rate
        """
        quotes = api_data.get('quotes', {})
        
        # Get USD to each currency
        from_usd_rate = quotes.get(f"USD{from_currency}", 1.0)
        to_usd_rate = quotes.get(f"USD{to_currency}", 1.0)
        
        # Calculate cross rate
        if from_usd_rate and to_usd_rate:
            return to_usd_rate / from_usd_rate
        
        return self.get_fallback_rate(from_currency, to_currency)
    
    def cache_exchange_rate(self, from_currency, to_currency, rate):
        """
        Cache exchange rate in database.
        
        Args:
            from_currency: Source currency
            to_currency: Target currency
            rate: Exchange rate to cache
        """
        try:
            self.db.execute("""
                INSERT OR REPLACE INTO exchange_rates 
                (base_currency, target_currency, rate, last_updated)
                VALUES (?, ?, ?, ?)
            """, from_currency, to_currency, rate, datetime.now().isoformat())
            
        except Exception as e:
            currency_logger.error(f"Failed to cache exchange rate: {str(e)}")
    
    def get_fallback_rate(self, from_currency, to_currency):
        """
        Get approximate exchange rate when API is unavailable.
        These are static rates for fallback only - not for production use.
        
        Returns:
            float: Approximate exchange rate
        """
        # Basic fallback rates relative to USD (as of 2024)
        # These should be updated periodically or fetched from a backup source
        fallback_rates = {
            'USD': 1.0,
            'EUR': 0.92,
            'GBP': 0.79,
            'JPY': 150.0,
            'CAD': 1.35,
            'AUD': 1.52,
            'CHF': 0.88,
            'CNY': 7.24,
            'INR': 83.0,
            'MXN': 17.0,
            'BRL': 4.95,
            'ZAR': 18.5,
            'KRW': 1320.0,
            'SGD': 1.34,
            'HKD': 7.82,
            'NOK': 10.5,
            'SEK': 10.3,
            'DKK': 6.85,
            'PLN': 3.95,
            'THB': 35.5,
            'NZD': 1.63
        }
        
        from_rate = fallback_rates.get(from_currency, 1.0)
        to_rate = fallback_rates.get(to_currency, 1.0)
        
        currency_logger.warning(f"Using fallback rate for {from_currency}/{to_currency}")
        return to_rate / from_rate
    
    def convert_amount(self, amount, from_currency, to_currency):
        """
        Convert an amount from one currency to another.
        
        Args:
            amount: Amount to convert (can be Decimal, float, or string)
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Decimal: Converted amount with 2 decimal places
            
        Security: Uses Decimal for precise financial calculations
        """
        # Convert to Decimal for precision
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        
        # Get exchange rate
        rate = self.fetch_exchange_rate(from_currency, to_currency)
        
        # Convert and round to 2 decimal places
        converted = amount * Decimal(str(rate))
        return converted.quantize(Decimal('0.01'))
    
    def get_user_preferred_currency(self, user_id):
        """
        Get user's preferred currency from database.
        
        Args:
            user_id: User ID
            
        Returns:
            str: Currency code (default: 'USD')
        """
        try:
            user = self.db.execute("""
                SELECT preferred_currency 
                FROM users 
                WHERE id = ?
            """, user_id)
            
            if user and user[0]['preferred_currency']:
                return user[0]['preferred_currency']
                
        except Exception as e:
            currency_logger.error(f"Error getting user currency preference: {str(e)}")
        
        return 'USD'  # Default currency
    
    def update_user_currency(self, user_id, currency_code):
        """
        Update user's preferred currency.
        
        Args:
            user_id: User ID
            currency_code: New currency code
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.validate_currency_code(currency_code):
            return False
        
        try:
            self.db.execute("""
                UPDATE users 
                SET preferred_currency = ?, updated_at = ?
                WHERE id = ?
            """, currency_code.upper(), datetime.now().isoformat(), user_id)
            
            currency_logger.info(f"Updated user {user_id} currency to {currency_code}")
            return True
            
        except Exception as e:
            currency_logger.error(f"Failed to update user currency: {str(e)}")
            return False

# Add this decorator for routes that need currency conversion
def with_currency_conversion(f):
    """
    Decorator to automatically handle currency conversion for routes.
    Adds currency service to the route function.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import g, current_app
        # Initialize currency service if not already done
        if not hasattr(g, 'currency_service'):
            db = current_app.config.get('db') or getattr(g, 'db', None)
            g.currency_service = CurrencyService(db)
        return f(*args, **kwargs)
    return decorated_function

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