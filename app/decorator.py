from functools import wraps
from pprint import pprint
from flask import request, jsonify,current_app
import jwt
from app.model import User


def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(' ')[1]  

        if not token:
            return {"error": "Token is missing!"}, 401

        try:
            # Decode the token using the secret key
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['sub'])  # Fetch user using the 'sub' claim (user ID)
            if not current_user:
                return {"error": "User is invalid"}, 401
        except Exception as e:
            return {"error": f"Token is invalid or expired: {str(e)}"}, 401

        # Pass current_user and other arguments to the wrapped function
        return f(*args, current_user=current_user, **kwargs)

    return decorated_function


def verify_superadmin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get the token from the Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token is missing or invalid."}), 401

        token = auth_header.split(" ")[1]
        try:
            # Decode the token
            decoded_token = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            # Check if the user has the superadmin role
            if 'roles' not in decoded_token or 'superadmin' not in decoded_token['roles']:
                return jsonify({"error": "You do not have the required permissions."}), 403
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token."}), 401

        # Call the actual route function
        return f(*args, **kwargs)

    return decorated_function


