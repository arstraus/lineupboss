# Analytics Module

This module provides analytics endpoints for the LineupBoss API.

## Overview
The analytics module provides data aggregation and statistical analysis for:
- Team performance metrics
- Player batting statistics
- Player fielding performance
- Rotational analytics

## Usage

### Prerequisites
Analytics functionality requires a Pro subscription tier. The endpoints will return
appropriate error messages for users without access to the advanced analytics feature.

### Endpoints

#### Team Analytics
- `GET /api/analytics/teams/{team_id}` - Get comprehensive team analytics
- `GET /api/analytics/teams/{team_id}/analytics` - Legacy endpoint, same as above

#### Batting Analytics
- `GET /api/analytics/teams/{team_id}/players/batting` - Get batting analytics for all players
- `GET /api/analytics/teams/{team_id}/batting-analytics` - Legacy endpoint, same as above

#### Fielding Analytics
- `GET /api/analytics/teams/{team_id}/players/fielding` - Get fielding analytics for all players
- `GET /api/analytics/teams/{team_id}/fielding-analytics` - Legacy endpoint, same as above

#### Debug
- `GET /api/analytics/status` - Simple health check for analytics module
- `GET /api/analytics/teams/{team_id}/debug` - Detailed diagnostics on analytics data

## Implementation Notes

- All analytics endpoints require JWT authentication
- Advanced analytics features are restricted to Pro subscription tier
- Error handling follows the standard API error response format
- The module uses the `AnalyticsService` for data processing

## Future Improvements
- Add player-specific analytics routes (e.g., `/api/analytics/players/{player_id}`)
- Add date range filtering for all analytics queries
- Add export functionality for analytics data
- Implement analytics caching for better performance