from app import create_app
from app.models import db, User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    print("Creating tables...")
    db.create_all()
    print("Tables created.")
    
    if not User.query.first():
        print("Creating default superadmin account...")
        hashed_pw = generate_password_hash('admin')
        admin_user = User(username='admin', password_hash=hashed_pw, role='superadmin')
        db.session.add(admin_user)
        db.session.commit()
        print("Default superadmin 'admin' created.")
    else:
        print("Superadmin already exists.")
