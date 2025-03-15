# LineupBoss - Baseball Lineup Management

A comprehensive baseball lineup management application for coaches to create fair and balanced team rotations.

![LineupBoss](https://github.com/your-username/lineupboss/raw/main/screenshot.png)

> **LineupBoss** helps youth baseball coaches create balanced batting orders and field rotations that give every player fair playing time while optimizing team performance.

## Key Features

- **Team Management**: Create and manage multiple teams, each with their own roster of players
- **Game Scheduling**: Organize your season with an intuitive game scheduling system
- **Player Availability Tracking**: Easily mark which players are available for each game
- **Smart Batting Order**: Create fair batting orders that ensure equal opportunities across games
- **Intelligent Fielding Rotations**: Assign positions for each inning with fairness validation
- **Position Balance Analysis**: Get insights into how playing time is distributed across positions
- **Game-Day Plans**: Generate and export lineup sheets as PDFs for coaches and parents
- **Data Persistence**: All your team and game data is securely stored and accessible anytime
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **User Authentication**: Secure access with JWT-based authentication and user accounts

## Technical Architecture

LineupBoss employs a modern, maintainable architecture:

### Backend (Python/Flask)
- **RESTful API**: Well-structured endpoints following REST principles
- **JWT Authentication**: Secure token-based authentication system
- **SQLAlchemy ORM**: Robust database interaction with PostgreSQL
- **Service Layer**: Organized business logic in dedicated services
- **API Documentation**: Interactive Swagger documentation
- **Error Handling**: Comprehensive error handling and reporting

### Frontend (React/JavaScript)
- **Component Architecture**: Reusable, modular React components
- **State Management**: Efficient React hooks-based state management
- **Bootstrap UI**: Responsive design with Bootstrap 5 components
- **Axios HTTP Client**: Streamlined API communication
- **JWT Integration**: Secure auth token management
- **Form Validation**: Client-side validation for all input forms
- **PDF Export**: Generate downloadable game plans with HTML2PDF

### Cross-Cutting Concerns
- **Shared Models**: Common data models between frontend and backend
- **Consistent Error Handling**: Standardized error responses and handling
- **Responsive Design**: Mobile-first approach for all user interfaces

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL database
- Git

### Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/your-username/lineupboss.git
   cd lineupboss
   ```

2. **Database Setup:**
   ```bash
   # Create PostgreSQL database
   createdb lineup

   # Optional: Restore from database dump if you have one
   # psql lineup < backup.sql
   ```

3. **Backend Setup:**
   ```bash
   # Install backend requirements
   pip install -r backend/requirements.txt

   # Configure environment variables
   cat > .env << EOF
   DATABASE_URL=postgresql://username:password@localhost/lineup
   JWT_SECRET_KEY=$(openssl rand -hex 32)
   EOF

   # Initialize the database
   python migrate_db.py
   ```

4. **Frontend Setup:**
   ```bash
   # Navigate to frontend directory
   cd frontend

   # Install dependencies
   npm install

   # Configure API URL for development
   echo "REACT_APP_API_URL=http://localhost:5000/api" > .env
   ```

### Running the Application

**Option 1: Run backend and frontend separately**
```bash
# Terminal 1 - Backend
cd backend
gunicorn app:app --reload

# Terminal 2 - Frontend
cd frontend
npm start
```

**Option 2: Run everything with one command**
```bash
# From the project root
npm run start:dev
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000/api
- API Documentation: http://localhost:5000/api/docs

## How to Use LineupBoss

### 1. Account Setup
1. **Register or Login**: Create your account or log in with existing credentials
2. **Dashboard**: View all your teams on the dashboard after logging in

### 2. Team Management
1. **Create Team**: Set up your team with name, league, and coach information
2. **Add Players**: Create player profiles with names and jersey numbers
3. **Manage Roster**: Edit or remove players as needed

### 3. Game Scheduling
1. **Add Games**: Create game entries with dates, times, and opponents
2. **View Schedule**: See your entire season laid out chronologically
3. **Game Numbers**: Each game has a number that keeps them in order

### 4. Game Preparation
1. **Player Availability**: Mark which players will be available for each game
2. **Batting Order**: Create a fair batting lineup from available players
3. **Fielding Rotations**: Assign defensive positions for each inning
   - Color coding indicates position balance issues
   - Validation ensures no player plays the same position multiple times
   - System warns about consecutive infield/outfield assignments

### 5. Game Day
1. **Game Summary**: View the complete lineup card with all assignments
2. **PDF Export**: Generate a printable PDF of your game plan
3. **Mobile Access**: Access lineups from your phone during the game

### 6. Season Management
1. **Fairness Analysis**: Review position distribution across the season
2. **Adjustment Tools**: Easily modify lineups based on analysis
3. **Historical Data**: Access previous game plans throughout the season

## Deployment Guide

### Backend Deployment Options

#### Option 1: Heroku
```bash
# Login to Heroku
heroku login

# Create a new Heroku app
heroku create lineupboss-api

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:hobby-dev

# Set environment variables
heroku config:set JWT_SECRET_KEY=$(openssl rand -hex 32)

# Deploy backend
git subtree push --prefix backend heroku main

# Run database migrations
heroku run python migrate_db.py
```

#### Option 2: Railway
Railway offers an easy deployment option with PostgreSQL integration:
1. Connect your GitHub repository
2. Configure the build and start commands
3. Add environment variables
4. Deploy with automatic CI/CD

### Frontend Deployment Options

#### Option 1: Netlify
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Build the frontend
cd frontend
npm run build

# Deploy to Netlify
netlify deploy --prod
```

#### Option 2: Vercel
1. Connect your GitHub repository to Vercel
2. Configure build settings:
   - Build Command: `cd frontend && npm run build`
   - Output Directory: `frontend/build`
3. Add environment variables:
   - REACT_APP_API_URL=https://your-backend-api.com/api

### Important Deployment Notes
- Ensure CORS is properly configured between frontend and backend
- Set appropriate environment variables for production
- Configure a proper domain for production use
- Enable HTTPS for secure communication

## Recent Improvements

### UI Enhancements (2025)
- **New Landing Page**: Baseball-themed landing page with clear features and benefits
- **Dashboard Redesign**: Streamlined dashboard with improved team management
- **Game Management**: Vertical game listing with sorting by game number
- **Fielding Rotations**: Enhanced position validation with clearer visual feedback
- **Mobile Responsiveness**: Improved layout for all screen sizes
- **Visual Consistency**: Unified design language across all app screens

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.