import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Complaint(db.Model):
    __tablename__ = 'complaints'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.UnicodeText, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.Unicode(20), default='pending')
    admin_reply = db.Column(db.UnicodeText, nullable=True)
    image_path = db.Column(db.Unicode(255), nullable=True)
    customer_name = db.Column(db.Unicode(100), nullable=True)
    account = db.Column(db.Unicode(100), nullable=True)
    department = db.Column(db.Unicode(100), nullable=True)
    email = db.Column(db.Unicode(100), nullable=True)
    user_id = db.Column(db.Integer, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'timestamp': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'status': self.status,
            'admin_reply': self.admin_reply,
            'image_path': self.image_path,
            'customer_name': self.customer_name,
            'account': self.account,
            'department': self.department,
            'email': self.email,
            'user_id': self.user_id
        }

class AnalysisRecord(db.Model):
    __tablename__ = 'analysis_records'
    
    id = db.Column(db.Integer, primary_key=True)
    text_input = db.Column(db.UnicodeText, nullable=False)
    emotion_score = db.Column(db.Unicode(50), nullable=True)
    emotion_label = db.Column(db.Unicode(100), nullable=True)
    key_appeal = db.Column(db.UnicodeText, nullable=True)
    suggested_reply = db.Column(db.UnicodeText, nullable=True)
    analysis_result = db.Column(db.UnicodeText, nullable=True)
    chat_history = db.Column(db.UnicodeText, nullable=True, default='[]')
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'text_input': self.text_input,
            'emotion_score': self.emotion_score,
            'emotion_label': self.emotion_label,
            'key_appeal': self.key_appeal,
            'suggested_reply': self.suggested_reply,
            'analysis_result': self.analysis_result,
            'chat_history': self.chat_history,
            'timestamp': self.created_at.strftime('%Y-%m-%d %H:%M')
        }

class ChatRecord(db.Model):
    __tablename__ = 'chat_records'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Unicode(36), index=True, default=lambda: str(uuid.uuid4()))
    user_message = db.Column(db.UnicodeText, nullable=False)
    ai_response = db.Column(db.UnicodeText, nullable=False)
    file_path = db.Column(db.Unicode(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_message': self.user_message,
            'ai_response': self.ai_response,
            'file_path': self.file_path,
            'timestamp': self.created_at.strftime('%Y-%m-%d %H:%M')
        }

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Unicode(50), unique=True, nullable=False)
    password_hash = db.Column(db.Unicode(255), nullable=False)
    password_plain = db.Column(db.Unicode(255), nullable=True)
    role = db.Column(db.Unicode(20), default='admin') # 'superadmin', 'admin', or 'member'
    name = db.Column(db.Unicode(100), nullable=True)
    email = db.Column(db.Unicode(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'password_plain': self.password_plain,
            'role': self.role,
            'name': self.name,
            'email': self.email,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M')
        }



