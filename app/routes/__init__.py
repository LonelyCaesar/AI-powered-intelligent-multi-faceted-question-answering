from flask import Blueprint

# Initialize Blueprints
page_bp = Blueprint('pages', __name__)
auth_bp = Blueprint('auth', __name__)
chat_bp = Blueprint('chat', __name__, url_prefix='/api')
complaint_bp = Blueprint('complaints', __name__, url_prefix='/api')
analyze_bp = Blueprint('analyze', __name__, url_prefix='/api')
user_bp = Blueprint('users', __name__, url_prefix='/api')

# Import routes to register them with the blueprints
from app.routes import page_routes, auth_routes, chat_routes, complaint_routes, analyze_routes, user_routes
