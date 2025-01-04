from flask import Blueprint

# Create blueprint
survey_bp = Blueprint('survey', __name__)

# Import routes to associate with the blueprint
from . import routes