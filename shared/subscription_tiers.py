"""
Subscription tier definitions and feature access controls for LineupBoss.

This module defines the subscription tiers, their features, and related constants
that are used across both backend and frontend to control feature access.
"""

# Tier names (used in database)
TIER_ROOKIE = "rookie"
TIER_PRO = "pro"

# All available tiers as a list (in order of increasing capability)
ALL_TIERS = [TIER_ROOKIE, TIER_PRO]

# Tier feature definitions - maps each tier to its enabled features
TIER_FEATURES = {
    TIER_ROOKIE: {
        "max_teams": 2,
        "ai_lineup_generation": False,
        "advanced_analytics": False,
        "csv_import_export": True,     # Available to rookie tier
        "batch_availability_management": True,  # Available to rookie tier
        "export_pdfs": True,           # Available to rookie tier
    },
    TIER_PRO: {
        "max_teams": float("inf"),
        "ai_lineup_generation": True,
        "advanced_analytics": True,
        "csv_import_export": True,
        "batch_availability_management": True,
        "export_pdfs": True,
    }
}

# Tier pricing (monthly)
TIER_PRICING = {
    TIER_ROOKIE: 0.00,  # Free tier
    TIER_PRO: 9.99
}

# Tier descriptions for display
TIER_DESCRIPTIONS = {
    TIER_ROOKIE: "Basic lineup management for individual coaches (free)",
    TIER_PRO: "Advanced features for serious coaches and teams"
}

# Feature descriptions
FEATURE_DESCRIPTIONS = {
    "max_teams": "Number of teams you can manage",
    "ai_lineup_generation": "AI-powered fielding rotation suggestions",
    "advanced_analytics": "Advanced player and team analytics dashboard",
    "csv_import_export": "Import and export player data via CSV",
    "batch_availability_management": "Manage multiple player availability at once",
    "export_pdfs": "Export lineup cards and game plans as PDFs"
}

def has_feature(user_tier, feature_name):
    """Check if a tier has access to a specific feature.
    
    Args:
        user_tier (str): The user's subscription tier
        feature_name (str): The name of the feature to check
        
    Returns:
        bool: True if the tier has access to the feature
    """
    # Validate inputs
    if user_tier not in ALL_TIERS:
        # Default to rookie for unknown tiers
        user_tier = TIER_ROOKIE
        
    if feature_name not in FEATURE_DESCRIPTIONS:
        # Default to False for unknown features
        return False
        
    # Get the feature value
    return TIER_FEATURES[user_tier].get(feature_name, False)
    
def get_tier_index(tier_name):
    """Get the index of a tier in the ALL_TIERS list.
    
    Args:
        tier_name (str): The name of the tier
        
    Returns:
        int: The index of the tier (higher index = higher tier)
    """
    try:
        return ALL_TIERS.index(tier_name)
    except ValueError:
        # Default to lowest tier for unknown tiers
        return 0
        
def compare_tiers(user_tier, required_tier):
    """Compare two tiers to determine if user_tier is sufficient.
    
    Args:
        user_tier (str): The user's subscription tier
        required_tier (str): The required tier for a feature
        
    Returns:
        bool: True if user_tier is sufficient (greater than or equal to required_tier)
    """
    user_tier_index = get_tier_index(user_tier)
    required_tier_index = get_tier_index(required_tier)
    
    return user_tier_index >= required_tier_index