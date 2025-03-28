"""
Analytics module initialization.

This module exports the analytics blueprint for RESTful API endpoints.
"""
from flask import Blueprint

# Create the blueprint with unique name to avoid conflicts
analytics_bp = Blueprint('analytics_fixed', __name__)

# Import routes to register them with the blueprint
from api.analytics.routes import *