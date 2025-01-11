import os
from dotenv import load_dotenv

class Config:
    """Base configuration."""
    load_dotenv('.env')
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_default_secret_key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///users.db')  # Default to SQLite
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False
    TESTING = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 

    OTP_TIME = 30  # IN MINUTES
    TOKEN_TIME = 5 # IN HOURS

    INDEX_ROUTE = True
    
    LOGGING = True
    REQUEST_LOGGING = True
    RESPONSE_LOGGING = True

    SMS_SERVICE = True
    MAIL_SERVICE = True
    UHID_SERVICE = True
    CDAC_SERVICE = True

    SWAGGER_SERVICE = True
    OTP_SERVER = os.getenv('OTP_SERVER')
    OTP_USERNAME = os.getenv('OTP_USERNAME')
    OTP_PASSWORD = os.getenv('OTP_PASSWORD')
    OTP_ID = os.getenv('OTP_ID')
    OTP_SENDERID = os.getenv('OTP_SENDERID')



class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'a_strong_production_secret_key')
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test_users.db'  # Separate DB for testing
    DEBUG = True
