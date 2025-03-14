"""
API client for LineupBoss.

This module provides a unified client for accessing the LineupBoss API.
"""
import os
import requests
import json
from typing import Dict, List, Optional, Union, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LineupBossAPIClient:
    """Client for the LineupBoss API."""
    
    def __init__(self, base_url=None):
        """Initialize the API client.
        
        Args:
            base_url: The base URL of the API. If not provided, uses environment variable.
        """
        # Try to get from environment variable first
        self.base_url = base_url or os.getenv("API_URL")
            
        # Fallback to local API
        if not self.base_url:
            self.base_url = "http://localhost:5000/api"
            
        # Remove trailing slash if present
        if self.base_url and self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]
            
        # Initialize session and token
        self.session = requests.Session()
        self.token = None
        
    def set_token(self, token):
        """Set the authentication token.
        
        Args:
            token: The JWT token for authentication.
        """
        self.token = token
        
    def get_headers(self):
        """Get request headers with authentication token if available.
        
        Returns:
            dict: Headers for API requests.
        """
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
        
    def request(self, method, endpoint, data=None, params=None, token_required=True):
        """Make a request to the API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request payload
            params: Query parameters
            token_required: Whether authentication token is required
            
        Returns:
            Response data or error message
        """
        # Ensure endpoint starts with a slash
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"
            
        url = f"{self.base_url}{endpoint}"
        headers = self.get_headers()
        
        # Verify token if required
        if token_required and not self.token:
            return {"error": "Authentication required", "status_code": 401}
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = self.session.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers)
            else:
                return {"error": f"Unsupported method: {method}", "status_code": 400}
                
            # Handle response
            if response.status_code in (200, 201):
                return response.json()
            else:
                # Try to get error message from response
                try:
                    error_data = response.json()
                    error_message = error_data.get("error", response.text)
                except:
                    error_message = response.text
                    
                return {"error": error_message, "status_code": response.status_code}
                
        except requests.RequestException as e:
            return {"error": str(e), "status_code": 500}
            
    # Auth endpoints
    def register(self, email, password):
        """Register a new user.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            User data and access token or error
        """
        return self.request("POST", "/auth/register", {
            "email": email,
            "password": password
        }, token_required=False)
        
    def login(self, email, password):
        """Login a user.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            User data and access token or error
        """
        response = self.request("POST", "/auth/login", {
            "email": email,
            "password": password
        }, token_required=False)
        
        # If login successful, set token
        if "access_token" in response:
            self.set_token(response["access_token"])
            
        return response
        
    def get_current_user(self):
        """Get current user information.
        
        Returns:
            User data or error
        """
        return self.request("GET", "/auth/me")
        
    # Team endpoints
    def get_teams(self):
        """Get all teams for the current user.
        
        Returns:
            List of teams or error
        """
        return self.request("GET", "/teams/")
        
    def get_team(self, team_id):
        """Get a specific team.
        
        Args:
            team_id: Team ID
            
        Returns:
            Team data or error
        """
        return self.request("GET", f"/teams/{team_id}/")
        
    def create_team(self, team_data):
        """Create a new team.
        
        Args:
            team_data: Team data including name, league, etc.
            
        Returns:
            Created team data or error
        """
        return self.request("POST", "/teams/", team_data)
        
    def update_team(self, team_id, team_data):
        """Update a team.
        
        Args:
            team_id: Team ID
            team_data: Updated team data
            
        Returns:
            Updated team data or error
        """
        return self.request("PUT", f"/teams/{team_id}/", team_data)
        
    def delete_team(self, team_id):
        """Delete a team.
        
        Args:
            team_id: Team ID
            
        Returns:
            Success message or error
        """
        return self.request("DELETE", f"/teams/{team_id}/")
        
    # Player endpoints
    def get_players(self, team_id):
        """Get all players for a team.
        
        Args:
            team_id: Team ID
            
        Returns:
            List of players or error
        """
        return self.request("GET", f"/players/team/{team_id}")
        
    def get_player(self, player_id):
        """Get a specific player.
        
        Args:
            player_id: Player ID
            
        Returns:
            Player data or error
        """
        return self.request("GET", f"/players/{player_id}")
        
    def create_player(self, team_id, player_data):
        """Create a new player.
        
        Args:
            team_id: Team ID
            player_data: Player data
            
        Returns:
            Created player data or error
        """
        return self.request("POST", f"/players/team/{team_id}", player_data)
        
    def update_player(self, player_id, player_data):
        """Update a player.
        
        Args:
            player_id: Player ID
            player_data: Updated player data
            
        Returns:
            Updated player data or error
        """
        return self.request("PUT", f"/players/{player_id}", player_data)
        
    def delete_player(self, player_id):
        """Delete a player.
        
        Args:
            player_id: Player ID
            
        Returns:
            Success message or error
        """
        return self.request("DELETE", f"/players/{player_id}")
        
    # Game endpoints
    def get_games(self, team_id):
        """Get all games for a team.
        
        Args:
            team_id: Team ID
            
        Returns:
            List of games or error
        """
        return self.request("GET", f"/games/team/{team_id}")
        
    def get_game(self, game_id):
        """Get a specific game.
        
        Args:
            game_id: Game ID
            
        Returns:
            Game data or error
        """
        return self.request("GET", f"/games/{game_id}")
        
    def create_game(self, team_id, game_data):
        """Create a new game.
        
        Args:
            team_id: Team ID
            game_data: Game data
            
        Returns:
            Created game data or error
        """
        return self.request("POST", f"/games/team/{team_id}", game_data)
        
    def update_game(self, game_id, game_data):
        """Update a game.
        
        Args:
            game_id: Game ID
            game_data: Updated game data
            
        Returns:
            Updated game data or error
        """
        return self.request("PUT", f"/games/{game_id}", game_data)
        
    def delete_game(self, game_id):
        """Delete a game.
        
        Args:
            game_id: Game ID
            
        Returns:
            Success message or error
        """
        return self.request("DELETE", f"/games/{game_id}")
        
    # Batting order endpoints
    def get_batting_order(self, game_id):
        """Get batting order for a game.
        
        Args:
            game_id: Game ID
            
        Returns:
            Batting order data or error
        """
        return self.request("GET", f"/games/{game_id}/batting-order")
        
    def save_batting_order(self, game_id, order_data):
        """Save batting order for a game.
        
        Args:
            game_id: Game ID
            order_data: Batting order data (list of jersey numbers)
            
        Returns:
            Saved batting order data or error
        """
        return self.request("POST", f"/games/{game_id}/batting-order", {
            "order_data": order_data
        })
        
    # Fielding rotation endpoints
    def get_fielding_rotations(self, game_id):
        """Get fielding rotations for a game.
        
        Args:
            game_id: Game ID
            
        Returns:
            Fielding rotations data or error
        """
        return self.request("GET", f"/games/{game_id}/fielding-rotations")
        
    def save_fielding_rotation(self, game_id, inning, positions_data):
        """Save fielding rotation for a game inning.
        
        Args:
            game_id: Game ID
            inning: Inning number
            positions_data: Positions data
            
        Returns:
            Saved fielding rotation data or error
        """
        return self.request("POST", f"/games/{game_id}/fielding-rotations/{inning}", {
            "positions": positions_data
        })
        
    # Player availability endpoints
    def get_player_availability(self, game_id):
        """Get player availability for a game.
        
        Args:
            game_id: Game ID
            
        Returns:
            Player availability data or error
        """
        return self.request("GET", f"/games/{game_id}/player-availability")
        
    def save_player_availability(self, game_id, player_id, available, can_play_catcher=False):
        """Save player availability for a game.
        
        Args:
            game_id: Game ID
            player_id: Player ID
            available: Whether the player is available
            can_play_catcher: Whether the player can play catcher
            
        Returns:
            Saved player availability data or error
        """
        return self.request("POST", f"/games/{game_id}/player-availability/{player_id}", {
            "available": available,
            "can_play_catcher": can_play_catcher
        })
        
    def batch_save_player_availability(self, game_id, availability_data):
        """Batch save player availability for a game.
        
        Args:
            game_id: Game ID
            availability_data: Dictionary of player availability
            
        Returns:
            Saved player availability data or error
        """
        return self.request("POST", f"/games/{game_id}/player-availability/batch", 
                           availability_data)
        
# Create a singleton instance
api_client = LineupBossAPIClient()