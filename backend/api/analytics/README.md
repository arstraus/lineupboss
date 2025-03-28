# Analytics Module

This module provides analytics endpoints for the LineupBoss API.

## Endpoints

- GET /analytics/status - Check analytics service status
- GET /analytics/teams/{team_id} - Get team analytics
- GET /analytics/teams/{team_id}/players/batting - Get player batting analytics
- GET /analytics/teams/{team_id}/players/fielding - Get player fielding analytics

## Architecture

This module follows the package-based blueprint pattern described in the main API architecture guide:

1. `__init__.py` creates the blueprint and imports routes
2. `routes.py` defines endpoints using the blueprint from __init__

## Usage Example

```python
# Example API request to get team analytics
import requests

def get_team_analytics(team_id, token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"https://lineupboss.app/api/analytics/teams/{team_id}", headers=headers)
    return response.json()
```

## Implementation Notes

- Analytics data is computed on request, not stored in the database
- Most endpoints require the 'analytics' feature to be available in the user's subscription
- Time-intensive queries are optimized with caching and SQL query optimization
- Results are formatted for easy consumption by the frontend data visualization components