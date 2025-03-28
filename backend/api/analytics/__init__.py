"""
Analytics module initialization.

This module exports the analytics blueprint for RESTful API endpoints.
"""
from flask import Blueprint

# Create the blueprint
analytics_bp = Blueprint('analytics', __name__)

# Import routes to register them with the blueprint
# (import after creating blueprint to avoid circular imports)
from api.analytics.routes import *

# This package follows the standard blueprint pattern
# - Blueprint is created here
# - Routes are defined in routes.py
# - Routes are automatically registered when imported

# Include an additional variable to explicitly check for successful import
ANALYTICS_MODULE_LOADED = True