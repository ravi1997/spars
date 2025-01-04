from flask import Blueprint
from flask_restx import Namespace

# Create blueprint
survey_ns = Namespace('survey', description="Survey operations")

# Import routes to associate with the blueprint
from . import routes