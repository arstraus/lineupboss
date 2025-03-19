# LineupBoss API Routes Analysis

This document provides a comprehensive analysis of the LineupBoss API routes, identifying standard blueprint routes and emergency routes. The goal is to help plan a convergence strategy to standardize the API architecture and eliminate emergency routes over time.

## Overview

LineupBoss currently uses two parallel routing approaches:

1. **Standard Blueprint Routes**: Organized by resource type with consistent URL patterns
2. **Emergency Routes**: Double-prefixed `/api/api/` routes that provide backward compatibility

This dual routing approach was implemented to ensure service continuity during the transition period, but now needs consolidation.

## Blueprint Architecture

The application uses Flask blueprints for route organization, with the main API blueprint registered at `/api` and resource-specific blueprints registered under appropriate prefixes.

### Blueprint Registration

All blueprints are registered in `api/__init__.py` with the following URL prefix hierarchy:

```
/api                   - Main API blueprint (api)
  /                    - System endpoints (system)
  /auth                - Authentication endpoints (auth)
  /user                - User profile endpoints (users_bp)
  /teams               - Team management (teams)
  /players             - Player management (players)
  /games               - Game management (games)
  /admin               - Admin functions (admin)
  /docs                - API documentation (docs)
```

Additionally, there are nested blueprints for relational endpoints:

```
/api
  /teams
    /<team_id>/games   - Games for a specific team (games_nested)
    /<team_id>/players - Players for a specific team (players_nested)
```

## Standard Routes by Blueprint

### System Blueprint (`/api`)

| Method | URL Pattern | Function | Description |
|--------|-------------|----------|-------------|
| GET | `/api` | `hello` | Root API endpoint |
| GET | `/api/test-jwt` | `test_jwt` | Test JWT validation |
| GET | `/api/test-db` | `test_db` | Test database connection |
| GET | `/api/health` | `health_check` | System health check |

### Authentication Blueprint (`/api/auth`)

| Method | URL Pattern | Function | Description |
|--------|-------------|----------|-------------|
| POST | `/api/auth/register` | `register` | Register a new user |
| POST | `/api/auth/login` | `login` | Login a user |
| POST | `/api/auth/refresh` | `refresh_token` | Refresh JWT token |
| GET | `/api/auth/me` | `get_user_info` | Get current user info |

### User Blueprint (`/api/user`)

| Method | URL Pattern | Function | Description |
|--------|-------------|----------|-------------|
| GET | `/api/user/profile` | `get_user_profile` | Get user profile |
| PUT | `/api/user/profile` | `update_user_profile` | Update user profile |
| PUT | `/api/user/password` | `update_password` | Update password |
| GET | `/api/user/subscription` | `get_subscription` | Get subscription info |

### Teams Blueprint (`/api/teams`)

| Method | URL Pattern | Function | Description |
|--------|-------------|----------|-------------|
| GET | `/api/teams` | `get_teams` | Get all teams for current user |
| POST | `/api/teams` | `create_team` | Create a new team |
| GET | `/api/teams/<team_id>` | `get_team` | Get specific team |
| PUT | `/api/teams/<team_id>` | `update_team` | Update team |
| DELETE | `/api/teams/<team_id>` | `delete_team` | Delete team |

### Players Blueprint (`/api/players`)

| Method | URL Pattern | Function | Description |
|--------|-------------|----------|-------------|
| GET | `/api/players/<player_id>` | `get_player` | Get specific player |
| PUT | `/api/players/<player_id>` | `update_player` | Update player |
| DELETE | `/api/players/<player_id>` | `delete_player` | Delete player |
| GET | `/api/players/team/<team_id>` | `get_players_legacy` | Get players (legacy) |
| POST | `/api/players/team/<team_id>` | `create_player` | Create player (legacy) |

### Games Blueprint (`/api/games`)

| Method | URL Pattern | Function | Description |
|--------|-------------|----------|-------------|
| GET | `/api/games/<game_id>` | `get_game` | Get specific game |
| PUT | `/api/games/<game_id>` | `update_game` | Update game |
| DELETE | `/api/games/<game_id>` | `delete_game` | Delete game |
| GET | `/api/games/team/<team_id>` | `get_games_legacy` | Get games for team (legacy) |
| POST | `/api/games/team/<team_id>` | `create_game` | Create game (legacy) |
| GET | `/api/games/<game_id>/batting-order` | `get_batting_order` | Get batting order |
| POST, PUT | `/api/games/<game_id>/batting-order` | `save_batting_order` | Save batting order |
| GET | `/api/games/<game_id>/fielding-rotations` | `get_fielding_rotations` | Get fielding rotations |
| GET, POST, PUT | `/api/games/<game_id>/fielding-rotations/<inning>` | `fielding_rotation_by_inning` | Get/save fielding by inning |
| GET | `/api/games/<game_id>/player-availability` | `get_player_availability` | Get player availability |
| GET, POST, PUT | `/api/games/<game_id>/player-availability/<player_id>` | `player_availability_by_id` | Get/save player availability |
| POST | `/api/games/<game_id>/player-availability/batch` | `batch_save_player_availability` | Batch update availability |
| POST | `/api/games/<game_id>/ai-fielding-rotation` | `generate_ai_fielding_rotation` | Generate AI fielding rotation |

### Admin Blueprint (`/api/admin`)

| Method | URL Pattern | Function | Description |
|--------|-------------|----------|-------------|
| GET | `/api/admin/users` | `get_users` | Get all users |
| POST | `/api/admin/users/<user_id>/approve` | `approve_user` | Approve user |
| POST | `/api/admin/users/<user_id>/reject` | `reject_user` | Reject user |
| DELETE | `/api/admin/users/<user_id>` | `delete_user` | Delete user |
| PUT | `/api/admin/users/<user_id>/role` | `update_user_role` | Update user role |
| GET | `/api/admin/pending-count` | `get_pending_count` | Get pending registrations count |

### Nested-Route Blueprints

#### Games Nested (`/api/teams/<team_id>/games`)

| Method | URL Pattern | Function | Description |
|--------|-------------|----------|-------------|
| GET | `/api/teams/<team_id>/games` | `get_games` | Get all games for a team |

#### Players Nested (`/api/teams/<team_id>/players`)

| Method | URL Pattern | Function | Description |
|--------|-------------|----------|-------------|
| GET | `/api/teams/<team_id>/players` | `get_players` | Get all players for a team |
| POST | `/api/teams/<team_id>/players` | `create_player` | Create a player for a team |

## Emergency Routes

The following emergency routes all use the `/api/api/` double-prefix pattern and are implemented in `app.py`. They serve as temporary handlers to ensure backward compatibility during the migration.

### Authentication Emergency Routes

| Method | URL Pattern | Function | Description |
|--------|-------------|----------|-------------|
| POST | `/api/api/auth/login` | `fix_double_api_prefix_login` | Login handler |
| POST | `/api/api/auth/register` | `fix_double_api_prefix_register` | Registration handler |
| GET | `/api/api/auth/me` | `fix_double_api_prefix_me` | Current user info handler |
| POST | `/api/api/auth/refresh` | `fix_double_api_prefix_refresh` | Token refresh handler |

### User Emergency Routes

| Method | URL Pattern | Function | Description |
|--------|-------------|----------|-------------|
| GET | `/api/api/user/profile` | `fix_double_api_prefix_get_profile` | Get profile handler |
| PUT | `/api/api/user/profile` | `fix_double_api_prefix_update_profile` | Update profile handler |
| GET | `/api/api/user/subscription` | `fix_double_api_prefix_get_subscription` | Get subscription handler |

### Team Emergency Routes

| Method | URL Pattern | Function | Description |
|--------|-------------|----------|-------------|
| GET | `/api/api/teams` | `fix_double_api_prefix_get_teams` | Get teams handler |
| GET | `/api/api/teams/<team_id>` | `fix_double_api_prefix_get_team` | Get team handler |
| POST | `/api/api/teams` | `fix_double_api_prefix_create_team` | Create team handler |

### Admin Emergency Routes

| Method | URL Pattern | Function | Description |
|--------|-------------|----------|-------------|
| GET | `/api/api/admin/pending-count` | `fix_double_api_prefix_pending_count` | Get pending count handler |
| GET | `/api/api/admin/users` | `fix_double_api_prefix_get_users` | Get users handler |
| POST | `/api/api/admin/users/<user_id>/approve` | `fix_double_api_prefix_approve_user` | Approve user handler |
| POST | `/api/api/admin/users/<user_id>/reject` | `fix_double_api_prefix_reject_user` | Reject user handler |
| DELETE | `/api/api/admin/users/<user_id>` | `fix_double_api_prefix_delete_user` | Delete user handler |
| PUT | `/api/api/admin/users/<user_id>/role` | `fix_double_api_prefix_update_user_role` | Update role handler |

### Players Emergency Routes

| Method | URL Pattern | Function | Description |
|--------|-------------|----------|-------------|
| GET | `/api/api/teams/<team_id>/players` | `fix_double_api_prefix_get_players` | Get players handler |
| GET | `/api/api/players/<player_id>` | `fix_double_api_prefix_get_player` | Get player handler |
| GET | `/api/api/players/team/<team_id>` | `fix_double_api_prefix_get_players_legacy` | Get players legacy handler |

### Games Emergency Routes

| Method | URL Pattern | Function | Description |
|--------|-------------|----------|-------------|
| GET | `/api/api/teams/<team_id>/games` | `fix_double_api_prefix_get_games` | Get games handler |
| GET | `/api/api/games/<game_id>` | `fix_double_api_prefix_get_game` | Get game handler |
| GET, POST | `/api/api/games/team/<team_id>` | `fix_double_api_prefix_games_team_operations` | Games team operations handler |
| GET, POST, PUT | `/api/api/games/<game_id>/batting-order` | `fix_double_api_prefix_batting_order` | Batting order handler |
| GET | `/api/api/games/<game_id>/fielding-rotations` | `fix_double_api_prefix_get_fielding_rotations` | Get fielding rotations handler |
| GET, POST, PUT | `/api/api/games/<game_id>/fielding-rotations/<inning>` | `fix_double_api_prefix_fielding_rotation_by_inning` | Fielding rotation handler |
| GET, PUT, POST | `/api/api/games/<game_id>/player-availability` | `fix_double_api_prefix_player_availability` | Player availability handler |
| POST | `/api/api/games/<game_id>/player-availability/batch` | `fix_double_api_prefix_batch_player_availability` | Batch availability handler |
| GET, POST, PUT | `/api/api/games/<game_id>/player-availability/<player_id>` | `fix_double_api_prefix_player_availability_by_id` | Individual player availability |
| POST | `/api/api/games/<game_id>/ai-fielding-rotation` | `fix_double_api_prefix_generate_ai_fielding_rotation` | AI fielding rotation handler |

## Frontend API Client Implementation

The frontend handles these dual routing patterns through a dedicated API client in `api.js` that normalizes paths to prevent double prefixing. Key features include:

1. **Path Normalization**: The `apiPath()` function handles path normalization to ensure consistent prefixing.
2. **Duplicate Prefix Detection**: The client detects and fixes `/api/api/` patterns.
3. **Safe Request Methods**: Wrapped request methods use the path normalization to ensure consistency.

However, there are inconsistencies in how different service files interact with the API:

1. **Different URL Patterns**:
   - For player operations, some services use `/teams/${teamId}/players` while others use `/players/team/${teamId}`
   - For game operations, services consistently use `/games/team/${teamId}` (legacy route), but the backend also supports `/teams/${teamId}/games` (nested route)

2. **Direct API Calls**: Some components bypass the API wrapper functions, making direct Axios calls that don't benefit from path normalization.

## Route Pattern Concerns

The codebase exhibits three distinct route pattern styles:

1. **Resource-specific routes**: `/games/team/{team_id}` (legacy style)
2. **Nested resource routes**: `/teams/{team_id}/games` (REST style)
3. **Double-prefixed emergency routes**: `/api/api/games/team/{team_id}` (temporary)

This mixed approach creates confusion and maintenance challenges.

## Convergence Strategy Recommendations

### 1. Standardize on REST-Style Nested Routes

Adopt a consistent REST-style approach with properly nested resources:
- `/teams/{team_id}/players` instead of `/players/team/{team_id}`
- `/teams/{team_id}/games` instead of `/games/team/{team_id}`

### 2. Frontend Migration Approach

1. Update frontend services to use consistent API patterns:
   - Modify all service files to use the same URL structure for the same operations
   - Update components that make direct API calls to use the API client wrapper

2. Create an API version constant to manage transitions:
   ```javascript
   // In constants.js
   export const API_VERSION = 'v1';

   // In api.js
   import { API_VERSION } from '../constants';
   const apiPath = (path) => {
     // Use versioned API paths
     return `/api/${API_VERSION}${path}`;
   };
   ```

3. Deploy frontend changes that use the standardized routes, maintaining backward compatibility through the API client's normalization logic.

### 3. Backend Transition Strategy

1. Add API version prefix support in app.py and blueprint registration:
   ```python
   # In api/__init__.py
   api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')
   register_blueprint(api_v1, 'teams', 'teams', '/teams')
   ```

2. Keep emergency routes and legacy routes during a transitional period with clear deprecation notices.

3. Implement route usage metrics to track which routes are still being used by clients.

4. Set a timeline for gradual removal of emergency routes and eventual legacy route deprecation.

### 4. Documentation and Deprecation Timeline

1. **Phase 1 (Immediate)**: Document all routes and mark emergency routes as deprecated in API docs.
2. **Phase 2 (1-2 months)**: Deploy updated frontend with standardized route usage.
3. **Phase 3 (3 months)**: Add deprecation warnings in API responses for legacy routes.
4. **Phase 4 (6 months)**: Remove emergency routes but maintain legacy routes with warnings.
5. **Phase 5 (12 months)**: Complete migration to standardized REST-style routes only.

## Conclusion

The LineupBoss API currently uses a mix of routing patterns to ensure backward compatibility. A phased approach to standardizing on REST-style nested routes will improve code maintainability, simplify API interactions, and reduce confusion. This strategy allows for a smooth transition while maintaining compatibility for existing clients.