# LineupBoss API Architecture

This document describes the overall architecture of the LineupBoss API, including route organization, authentication, and best practices for extending the API.

## Route Organization

The API follows a standardized blueprint-based architecture where all routes are organized by functional domain:

| Domain | Blueprint | Prefix | Description |
|--------|-----------|--------|-------------|
| System | system | `/api/` | Core system endpoints (health checks, info) |
| Auth | auth | `/api/auth/` | Authentication (login, register, token refresh) |
| User | users_bp | `/api/user/` | User profile management |
| Teams | teams | `/api/teams/` | Team management endpoints |
| Players | players | `/api/players/` | Player management endpoints |
| Games | games | `/api/games/` | Game management endpoints |
| Admin | admin | `/api/admin/` | Administrative functions |
| Docs | docs | `/api/docs/` | API documentation |

### Blueprint Registration

All blueprints are registered in the `api/__init__.py` file with the appropriate prefixes. The main API blueprint has the `/api` prefix, and all other blueprints are registered with it.

Blueprint registration follows this structure:
```python
# Register blueprint with error handling
register_blueprint(api, 'module_name', 'blueprint_name', '/prefix')
```

### Deprecated Routes

Some legacy routes defined directly in `app.py` are maintained for backward compatibility. These routes forward requests to the corresponding blueprint routes and will be removed in a future release.

## Authentication

The API uses JWT (JSON Web Tokens) for authentication:

1. **Token Acquisition**: Clients obtain a token by calling `/api/auth/login` or `/api/auth/register`
2. **Token Usage**: The token is included in the `Authorization` header as `Bearer {token}`
3. **Token Refresh**: Tokens can be refreshed by calling `/api/auth/refresh`
4. **Token Protection**: Routes requiring authentication use the `@jwt_required()` decorator
5. **Permission Control**: Admin routes use the admin-specific decorators

### Token Flow

```
┌─────────┐  1. Login Request   ┌─────────┐
│         ├───────────────────► │         │
│ Client  │ 2. Returns JWT      │ Server  │
│         │◄───────────────────┤         │
└────┬────┘                     └─────────┘
     │                              ▲
     │                              │
     │ 3. API Request with JWT      │
     │ in Authorization header      │
     │                              │
     ▼                              │
┌─────────┐                     ┌─────────┐
│Protected│  4. Returns Data    │JWT Auth │
│Resource │◄────────────────────┤Middleware│
└─────────┘                     └─────────┘
```

## Database Access

The API uses a standardized database access pattern:

1. **Context Manager**: All database access uses the `db_session` context manager
2. **Read-Only Flag**: Read operations specify `read_only=True`
3. **Commit Flag**: Write operations specify `commit=True`
4. **Service Pattern**: 
   - Controller code (API routes) handle transaction boundaries (commits)
   - Service layer handles business logic
   - Services flush but never commit

Example:
```python
# Read operation
with db_session(read_only=True) as session:
    data = session.query(Model).all()

# Write operation
with db_session(commit=True) as session:
    entity = Model(...)
    session.add(entity)
    # No need to commit - handled by context manager
```

## Error Handling

The API uses standardized error handling:

1. **Error Response**: Use `db_error_response(e, "Error message")` for database errors
2. **HTTP Status Codes**: Use appropriate HTTP status codes (400 for client errors, 500 for server errors)
3. **JSON Response**: All errors return a JSON response with an `error` field

## Extending the API

To add new API endpoints:

1. Determine which blueprint the endpoint belongs to, or create a new one
2. Define the route using the blueprint's `route` decorator
3. Implement the route function
4. Register the blueprint in `api/__init__.py` if it's new

Example of a new endpoint:
```python
@blueprint.route('/new-endpoint', methods=['GET'])
@jwt_required()  # If authentication is required
def new_endpoint():
    try:
        with db_session(read_only=True) as session:
            # Implement endpoint logic
            return jsonify({'result': 'success'})
    except Exception as e:
        return db_error_response(e, "Error message")
```

### Best Practices

- Use descriptive route names that reflect the resource and action
- Use appropriate HTTP methods (GET, POST, PUT, DELETE)
- Always validate input data
- Use query parameters for filtering, sorting, and pagination
- Use path parameters for resource identification
- Return appropriate HTTP status codes
- Document all endpoints
- Follow REST principles
- Use consistent response formats