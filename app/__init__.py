from flask import Flask
from app.config import config_by_name
from app.models import db

def create_app(config_name='development'):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    # Load config
    app.config.from_object(config_by_name[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    from app.routes import page_bp, auth_bp, chat_bp, complaint_bp, analyze_bp, user_bp
    app.register_blueprint(page_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(complaint_bp)
    app.register_blueprint(analyze_bp)
    app.register_blueprint(user_bp)
    
    # Create tables
    with app.app_context():
        db.create_all()
        
        # Auto-migration for missing columns in chat_records and analysis_records
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        
        with db.engine.begin() as conn:
            if inspector.has_table('chat_records'):
                columns = [col['name'] for col in inspector.get_columns('chat_records')]
                if 'session_id' not in columns:
                    if db.engine.url.drivername.startswith('mssql'):
                        conn.execute(text("ALTER TABLE chat_records ADD session_id NVARCHAR(36);"))
                    else:
                        conn.execute(text("ALTER TABLE chat_records ADD COLUMN session_id VARCHAR(36);"))
                
                if 'file_path' not in columns:
                    if db.engine.url.drivername.startswith('mssql'):
                        conn.execute(text("ALTER TABLE chat_records ADD file_path NVARCHAR(255);"))
                    else:
                        conn.execute(text("ALTER TABLE chat_records ADD COLUMN file_path VARCHAR(255);"))
                        
                if db.engine.url.drivername.startswith('mssql'):
                    try:
                        conn.execute(text("ALTER TABLE chat_records ALTER COLUMN user_message NVARCHAR(MAX) NOT NULL;"))
                        conn.execute(text("ALTER TABLE chat_records ALTER COLUMN ai_response NVARCHAR(MAX) NOT NULL;"))
                    except Exception as e:
                        print(f"Could not alter chat_records to NVARCHAR: {e}")


            if inspector.has_table('complaints'):
                columns = [col['name'] for col in inspector.get_columns('complaints')]
                
                # Add missing columns
                missing_cols = []
                if 'image_path' not in columns: missing_cols.append("ADD image_path NVARCHAR(255)")
                if 'customer_name' not in columns: missing_cols.append("ADD customer_name NVARCHAR(100)")
                if 'account' not in columns: missing_cols.append("ADD account NVARCHAR(100)")
                if 'department' not in columns: missing_cols.append("ADD department NVARCHAR(100)")
                if 'email' not in columns: missing_cols.append("ADD email NVARCHAR(100)")
                if 'user_id' not in columns: missing_cols.append("ADD user_id INT")
                
                if missing_cols and db.engine.url.drivername.startswith('mssql'):
                    try:
                        for col_stmt in missing_cols:
                            conn.execute(text(f"ALTER TABLE complaints {col_stmt};"))
                    except Exception as e:
                        print(f"Could not add missing columns to complaints: {e}")
                        
                if db.engine.url.drivername.startswith('mssql'):
                    try:
                        conn.execute(text("ALTER TABLE complaints ALTER COLUMN content NVARCHAR(MAX) NOT NULL;"))
                        conn.execute(text("ALTER TABLE complaints ALTER COLUMN admin_reply NVARCHAR(MAX) NULL;"))
                    except Exception as e:
                        print(f"Could not alter complaints to NVARCHAR: {e}")

            if inspector.has_table('analysis_records'):
                columns = [col['name'] for col in inspector.get_columns('analysis_records')]
                if 'key_appeal' not in columns:
                    if db.engine.url.drivername.startswith('mssql'):
                        try:
                            conn.execute(text("ALTER TABLE analysis_records ADD key_appeal NVARCHAR(MAX) NULL;"))
                        except Exception: pass
                if 'suggested_reply' not in columns:
                    if db.engine.url.drivername.startswith('mssql'):
                        try:
                            conn.execute(text("ALTER TABLE analysis_records ADD suggested_reply NVARCHAR(MAX) NULL;"))
                        except Exception: pass
                if 'chat_history' not in columns:
                    if db.engine.url.drivername.startswith('mssql'):
                        try:
                            conn.execute(text("ALTER TABLE analysis_records ADD chat_history NVARCHAR(MAX) NULL;"))
                        except Exception as e:
                            print(f"Could not add chat_history to analysis_records: {e}")
                    else:
                        try:
                            conn.execute(text("ALTER TABLE analysis_records ADD COLUMN chat_history TEXT DEFAULT '[]';"))
                        except Exception as e:
                            pass
            if inspector.has_table('users'):
                columns = [col['name'] for col in inspector.get_columns('users')]
                
                missing_cols = []
                if 'password_plain' not in columns: missing_cols.append("ADD COLUMN password_plain VARCHAR(255)")
                if 'role' not in columns: missing_cols.append("ADD COLUMN role VARCHAR(20) DEFAULT 'admin'")
                if 'name' not in columns: missing_cols.append("ADD COLUMN name VARCHAR(100)")
                if 'email' not in columns: missing_cols.append("ADD COLUMN email VARCHAR(100)")
                if 'created_at' not in columns: missing_cols.append("ADD COLUMN created_at DATETIME")
                
                if missing_cols:
                    for col_stmt in missing_cols:
                        if db.engine.url.drivername.startswith('mssql'):
                            # MSSQL syntax is slightly different
                            mssql_stmt = col_stmt.replace("ADD COLUMN", "ADD").replace("VARCHAR", "NVARCHAR")
                            try:
                                conn.execute(text(f"ALTER TABLE users {mssql_stmt};"))
                            except Exception as e:
                                print(f"Could not add missing columns to users: {e}")
                        else:
                            try:
                                conn.execute(text(f"ALTER TABLE users {col_stmt};"))
                            except Exception as e:
                                print(f"Could not add missing columns to users: {e}")
        
    return app
