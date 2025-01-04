from datetime import datetime, timedelta

from flask import current_app
import jwt


def generate_jwt_token(user):
    """Generate JWT token for the user"""
    SECRET_KEY = current_app.config['SECRET_KEY']  # Store this securely, ideally in environment variables
    expiration_time = datetime.utcnow() + timedelta(days=1)  # Token expires in 1 day
    payload = {
        'sub': user.id,  # 'sub' is the subject claim, i.e., the user ID
        'iat': datetime.utcnow(),  # Issued at time
        'exp': expiration_time  # Expiration time
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token