import os
from dotenv import load_dotenv

load_dotenv(override=True)

class Config:
    """Base configuration."""
    # 每次啟動時產生隨機金鑰，確保伺服器重啟 (Ctrl+C) 後，所有使用者的 Session 會自動失效並登出
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24).hex())
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configure SQLite database path (default to instance folder)
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    instance_dir = os.path.join(base_dir, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 
        f'sqlite:///{os.path.join(instance_dir, "complaints.db")}'
    )
    
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Dictionary to map environment to config class
config_by_name = dict(
    development=DevelopmentConfig,
    production=ProductionConfig,
    testing=TestingConfig
)
