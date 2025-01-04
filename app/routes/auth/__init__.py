from flask_restx import Namespace

# Create blueprint
auth_ns = Namespace('auth', description='Authentication related APIs')

# Import routes to associate with the blueprint
from . import routes