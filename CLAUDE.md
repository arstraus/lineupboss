# CLAUDE.md for Lineup Boss

## Build & Run Commands

### Backend
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Set up environment variables
# DATABASE_URL=postgresql://username:password@localhost/lineup
# JWT_SECRET_KEY=your_secret_key

# Run the API server
./run_server.sh
# or
cd backend && gunicorn app:app
```

### Frontend
```bash
# Install dependencies
cd frontend && npm install

# Run development server
npm start

# Build for production
npm run build
```

### Full Stack (Backend + Frontend)
```bash
# Install all dependencies
npm install

# Start development servers
npm run start:dev
```

## API Testing
```bash
# Get all teams
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/teams

# Create a team
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Tigers","league":"Little League"}' \
  http://localhost:5000/api/teams
```

## Code Style Guidelines

### Backend (Python)
- **Imports**: Group standard library, third-party, and local imports
- **Formatting**: Use 4 spaces for indentation
- **Naming**: snake_case for variables/functions, CamelCase for classes
- **Types**: Use type hints where appropriate
- **Error handling**: Use try/except blocks with specific exceptions
- **Constants**: Define constants at the top of files in UPPERCASE

### Database Access Patterns

#### Session Management
- Use the `db_session` context manager for database operations
- For read operations: `with db_session(read_only=True) as session:`
- For write operations: `with db_session(commit=True) as session:`
- Avoid direct use of `get_db()` and manual session closing

#### Error Handling
- Use standardized error handling with `db_error_response`
- Example:
  ```python
  try:
      with db_session(commit=True) as session:
          # database operations
  except Exception as e:
      return db_error_response(e, "Friendly error message")
  ```

#### Service Layer Responsibilities
- Services should not commit changes - only manipulate objects
- Controllers (API routes) are responsible for transaction boundaries
- Example service method:
  ```python
  @staticmethod
  def update_entity(session, entity_id, data):
      entity = session.query(Entity).get(entity_id)
      for key, value in data.items():
          setattr(entity, key, value)
      return entity
  ```

#### Utility Functions
- Use `db_get_or_404(session, Model, object_id)` for fetching by ID
- Use `db_run_transaction(func, *args, **kwargs)` for simple transactions

### Frontend (JavaScript/React)
- **Imports**: Group React, third-party, and local imports
- **Formatting**: Use 2 spaces for indentation
- **Naming**: camelCase for variables/functions, PascalCase for components
- **Types**: Use PropTypes or TypeScript for type checking
- **Error handling**: Use try/catch and proper error boundary components
- **Constants**: Define constants in dedicated files or at the top of components

## Key application constants
```javascript
// Position constants
export const POSITIONS = ["Pitcher", "Catcher", "1B", "2B", "3B", "SS", "LF", "RF", "LC", "RC", "Bench"];
export const INFIELD = ["Pitcher", "1B", "2B", "3B", "SS"];
export const OUTFIELD = ["Catcher", "LF", "RF", "LC", "RC"];
export const BENCH = ["Bench"];
```