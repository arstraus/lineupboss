#!/usr/bin/env python3
"""
Test script to diagnose analytics route issues.

This script tests the analytics route registration by directly 
importing the blueprint and checking its routes.
"""
import sys
import importlib
import inspect

try:
    # Try importing the analytics blueprint
    from backend.api.analytics import analytics_bp
    print("✅ Successfully imported analytics_bp from backend.api.analytics")
except ImportError:
    try:
        # Try without the 'backend' prefix
        from api.analytics import analytics_bp
        print("✅ Successfully imported analytics_bp from api.analytics")
    except ImportError as e:
        print(f"❌ Failed to import analytics_bp: {e}")
        sys.exit(1)

# Check if the analytics_bp has routes (deferred_functions)
if not hasattr(analytics_bp, 'deferred_functions'):
    print("❌ analytics_bp has no deferred_functions (no routes)")
    sys.exit(1)

print(f"\nBlueprint name: {analytics_bp.name}")
print(f"URL prefix: {analytics_bp.url_prefix}")

# List all routes in the blueprint
print("\nRoutes in analytics_bp:")
routes_count = 0
for func in analytics_bp.deferred_functions:
    routes_count += 1
    if hasattr(func, '__name__'):
        print(f"  - Function: {func.__name__}")
    else:
        print(f"  - Function: {func}")

if routes_count == 0:
    print("❌ No routes found in the analytics blueprint")
else:
    print(f"✅ Found {routes_count} routes in the analytics blueprint")

# Verify view functions are correctly attached to the blueprint
print("\nChecking for route functions in analytics.routes:")

try:
    if 'api.analytics.routes' in sys.modules:
        routes_module = sys.modules['api.analytics.routes']
    else:
        routes_module = importlib.import_module('api.analytics.routes')
    
    print("✅ Successfully imported routes module")
    
    # Find all functions in the routes module with blueprint.route decorators
    route_functions = []
    for name, func in inspect.getmembers(routes_module, inspect.isfunction):
        if name.startswith('get_') or name.endswith('_analytics') or '_analytics_' in name:
            route_functions.append(name)
    
    print(f"\nPotential route functions in the module:")
    for func_name in route_functions:
        print(f"  - {func_name}")
        
except ImportError as e:
    print(f"❌ Failed to import routes module: {e}")

# Provide additional diagnostics
print("\nDiagnostic information:")
print(f"Python version: {sys.version}")
print(f"Module search paths:")
for path in sys.path:
    print(f"  - {path}")

print("\nSummary:")
if routes_count > 0:
    print("✅ Analytics routes are defined in the blueprint")
    print("🔍 Check application registration and URL prefixes")
else:
    print("❌ No analytics routes found in the blueprint")
    print("🔍 Check route definitions and circular imports")