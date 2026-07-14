from functools import wraps
from flask import session, redirect, url_for, request
from app.utils.response import error_response

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            if request.path.startswith('/api/'):
                return error_response('Unauthorized. Please log in.', status_code=401)
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def require_role(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('role') != role:
                if request.path.startswith('/api/'):
                    return error_response('Forbidden. Insufficient permissions.', status_code=403)
                return redirect(url_for('pages.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
