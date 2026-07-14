from flask import render_template, session, redirect, url_for
from app.routes import page_bp
from app.utils.auth import login_required

@page_bp.route('/')
@login_required
def index():
    return render_template('index.html')



@page_bp.route('/migrate')
def migrate():
    from app.models import db
    from sqlalchemy import text
    try:
        db.session.execute(text('ALTER TABLE complaints ADD COLUMN customer_name TEXT;'))
    except Exception as e: pass
    try:
        db.session.execute(text('ALTER TABLE complaints ADD COLUMN account TEXT;'))
    except Exception as e: pass
    try:
        db.session.execute(text('ALTER TABLE complaints ADD COLUMN department TEXT;'))
    except Exception as e: pass
    try:
        db.session.execute(text('ALTER TABLE complaints ADD COLUMN email TEXT;'))
    except Exception as e: pass
    db.session.commit()
    return "Migrated"
