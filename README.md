# LineupBoss - Baseball Lineup Manager

A modern baseball lineup management application with a React frontend and Flask API backend.

![LineupBoss](https://github.com/your-username/lineupboss/raw/main/screenshot.png)

## Features

- **Team Management**: Create and manage team roster with player names and jersey numbers
- **Game Scheduling**: Set up your season schedule with dates, times, and opponents
- **Player Availability**: Track which players are available for each game
- **Batting Order**: Create fair batting orders across all games
- **Fielding Rotation**: Assign fielding positions for each inning
- **Fairness Analysis**: Analyze how balanced your batting and fielding assignments are
- **Game Plans**: Generate and export game-day lineup sheets in PDF or text format
- **Data Management**: Save and load your team data for future use
- **Modern Web Interface**: Responsive React UI that works on desktop and mobile devices

## Architecture

LineupBoss uses a clean, modern architecture:

1. **Backend API** (Flask):
   - RESTful API for all data operations
   - JWT authentication for secure access
   - PostgreSQL database with SQLAlchemy ORM
   - Swagger documentation for API endpoints

2. **Frontend** (React):
   - Modern, responsive UI built with React
   - Bootstrap for styling and components
   - Axios for API communication
   - JWT authentication for user sessions

3. **Shared Code**:
   - Common database models
   - Shared configuration

## Installation

### Running the Full Stack (Backend API + React Frontend)

1. Clone this repository:
```bash
git clone https://github.com/your-username/lineupboss.git
cd lineupboss
```

2. Set up the backend:
```bash
# Install backend requirements
pip install -r backend/requirements.txt

# Set up environment variables
echo "DATABASE_URL=postgresql://username:password@localhost/lineup" > .env
echo "JWT_SECRET_KEY=your_secret_key" >> .env

# Start the API server
cd backend
gunicorn app:app
```

3. Set up the frontend:
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Configure API URL
echo "REACT_APP_API_URL=http://localhost:5000/api" > .env

# Start the development server
npm start
```

## Usage Guide

### Step 1: Setup
1. Create an account or log in to your existing account
2. Create a new team and enter team details
3. Add players to your roster with names and jersey numbers
4. Set up your game schedule with dates, times, and opponents

### Step 2: Create Lineups
1. Select a game from your schedule
2. Mark which players are available for the game
3. Create a batting order by dragging players to their positions
4. Assign fielding positions for each inning

### Step 3: Analyze Fairness
1. Use the Batting Analysis tool to ensure all players get opportunities in different batting positions
2. Check the Fielding Analysis to see how playing time is distributed across positions
3. Make adjustments to balance playing time across all games

### Step 4: Game Day
1. View your complete game plan including batting order and fielding assignments
2. Export your lineup as a PDF to share with coaches and players
3. Track actual playing time during the game (optional)

## Deployment

### Backend Deployment
The Flask backend can be deployed to any platform that supports Python:

#### Heroku Deployment
```bash
# From the backend directory
heroku create lineupboss-api
git subtree push --prefix backend heroku main

# Set environment variables
heroku config:set DATABASE_URL=your_postgresql_url
heroku config:set JWT_SECRET_KEY=your_jwt_secret
```

### Frontend Deployment
The React frontend can be deployed to Netlify, Vercel, or any static hosting:

#### Netlify Deployment
```bash
# From the frontend directory
npm run build
netlify deploy --prod
```
Remember to set the `REACT_APP_API_URL` to point to your deployed API.

## Requirements

- Python 3.8+ (for backend)
- Node.js 14+ (for frontend)
- PostgreSQL database
- See backend/requirements.txt and frontend/package.json for detailed dependencies