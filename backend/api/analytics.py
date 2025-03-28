"""
DISABLED: This module has been disabled due to route conflicts.

All code should import directly from the package:
from api.analytics import analytics_bp
"""

# Create a deprecated dummy blueprint without routes
# to avoid conflicts with the package implementation
from flask import Blueprint
analytics_bp = Blueprint('analytics_legacy', __name__)

# Include deprecation warning
import warnings
warnings.warn(
    "The 'api.analytics' module is deprecated and has been disabled. Import directly from the package instead: from api.analytics import analytics_bp",
    DeprecationWarning,
    stacklevel=2
)