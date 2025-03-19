# API Route Standardization

This document summarizes the changes made to standardize API routes in the LineupBoss frontend.

## Changes Made

1. Updated `playerGameServices.js` to use standardized REST-style routes:
   - Changed `get('/players/team/${teamId}')` to `get('/teams/${teamId}/players')`
   - Changed `post('/players/team/${teamId}', data)` to `post('/teams/${teamId}/players', data)`
   - Changed `get('/games/team/${teamId}')` to `get('/teams/${teamId}/games')`
   - Changed `post('/games/team/${teamId}', data)` to `post('/teams/${teamId}/games', data)`

2. Updated `api.js` to use consistent REST-style routes:
   - Changed `getGames(teamId)` to use `/teams/${teamId}/games`
   - Changed `createGame(teamId, data)` to use `/teams/${teamId}/games`

3. Improved `AuthContext.js`:
   - Replaced direct axios call with API client function `getPendingCount()`
   - Simplified error recovery logic that was previously handling dual route patterns
   - Removed unnecessary axios import

## Standard Route Patterns

All API routes now follow these standard patterns:

### Collection Resources
- GET `/api/teams` - Get all teams
- POST `/api/teams` - Create a team

### Single Resources
- GET `/api/teams/{id}` - Get a specific team
- PUT `/api/teams/{id}` - Update a team
- DELETE `/api/teams/{id}` - Delete a team

### Nested Resources
- GET `/api/teams/{id}/players` - Get players for a team
- POST `/api/teams/{id}/players` - Create a player for a team
- GET `/api/teams/{id}/games` - Get games for a team
- POST `/api/teams/{id}/games` - Create a game for a team

### Operations on Nested Resources
- GET `/api/games/{id}/batting-order` - Get batting order for a game
- POST `/api/games/{id}/batting-order` - Save batting order
- GET `/api/games/{id}/fielding-rotations` - Get all fielding rotations
- GET `/api/games/{id}/fielding-rotations/{inning}` - Get fielding for an inning
- POST `/api/games/{id}/fielding-rotations/{inning}` - Save fielding for an inning

## Future Work

While the frontend has been updated to use standard route patterns, the backend is still supporting both standard and legacy route patterns for backward compatibility. Once all clients are updated to use the new standardized routes, the legacy routes can be deprecated and eventually removed.

1. Update other clients (if any) that might be using the legacy route patterns
2. Monitor API usage to ensure all requests use standard routes
3. Add deprecation warnings to legacy route handlers
4. Gradually phase out legacy routes