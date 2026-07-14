from flask import render_template, request, session, redirect, url_for, flash
from app.utils.response import error_response
from app.routes import auth_bp

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        from app.models import User
        from werkzeug.security import check_password_hash
        
        user = User.query.filter_by(username=username).first()
        
        is_valid = False
        if user:
            try:
                is_valid = check_password_hash(user.password_hash, password)
            except ValueError:
                # Fallback or invalid hash format
                is_valid = False
        
        if user and is_valid:
            session.clear()
            session['logged_in'] = True
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['name'] = user.name
            session['email'] = user.email
            session.permanent = False
            
            return redirect(url_for('pages.index'))
        else:
            flash('帳號或密碼錯誤', 'danger')
            
    # Redirect if already logged in
    if session.get('logged_in'):
        return redirect(url_for('pages.index'))
        
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('auth.login'))
