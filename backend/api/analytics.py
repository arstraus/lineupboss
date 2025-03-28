"""
DEPRECATED: This module has been migrated to a package structure.

This file exists only to maintain backward compatibility and redirect imports.
All new code should import directly from the package:

from api.analytics import analytics_bp
"""

# Redirect imports to the package
from api.analytics import analytics_bp
from api.analytics.routes import *

# Include deprecation warning
import warnings
warnings.warn(
    "The 'api.analytics' module is deprecated. Import directly from the package instead: from api.analytics import analytics_bp",
    DeprecationWarning,
    stacklevel=2
)