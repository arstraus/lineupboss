"""
Streamlit API wrapper for LineupBoss.

This module provides a transition layer for the Streamlit app to use the API client 
instead of direct database access.
"""
import pandas as pd
import streamlit as st
from typing import List, Dict, Any, Tuple, Optional

from shared.api_client import api_client

# Authentication functions
def login(email: str, password: str) -> Tuple[bool, str]:
    """Log in a user.
    
    Args:
        email: User email
        password: User password
        
    Returns:
        Tuple of (success, message)
    """
    response = api_client.login(email, password)
    
    if "error" in response:
        return False, response["error"]
        
    if "access_token" in response:
        # Store user info in session state
        st.session_state.user_id = response.get("user_id")
        st.session_state.is_authenticated = True
        st.session_state.user_email = email
        st.session_state.api_token = response["access_token"]
        
        # Set token in API client
        api_client.set_token(response["access_token"])
        
        return True, "Login successful"
    
    return False, "Login failed"
    
def register(email: str, password: str) -> Tuple[bool, str]:
    """Register a new user.
    
    Args:
        email: User email
        password: User password
        
    Returns:
        Tuple of (success, message)
    """
    response = api_client.register(email, password)
    
    if "error" in response:
        return False, response["error"]
        
    if "access_token" in response:
        # Store user info in session state
        st.session_state.user_id = response.get("user_id")
        st.session_state.is_authenticated = True
        st.session_state.user_email = email
        st.session_state.api_token = response["access_token"]
        
        # Set token in API client
        api_client.set_token(response["access_token"])
        
        return True, "Registration successful"
    
    return False, "Registration failed"
    
def logout():
    """Log out the current user."""
    # Clear session state
    st.session_state.user_id = None
    st.session_state.is_authenticated = False
    st.session_state.user_email = None
    st.session_state.api_token = None
    
    # Clear API client token
    api_client.set_token(None)
    
# Team functions
def get_teams() -> List[Tuple[int, str]]:
    """Get all teams for the current user.
    
    Returns:
        List of tuples of (team_id, team_name)
    """
    response = api_client.get_teams()
    
    if "error" in response:
        st.error(f"Error getting teams: {response['error']}")
        return []
        
    # Convert to the expected format
    return [(team["id"], team["name"]) for team in response]
    
def get_teams_with_details() -> List[Dict[str, Any]]:
    """Get all teams with details for the current user.
    
    Returns:
        List of dictionaries with team details
    """
    response = api_client.get_teams()
    
    if "error" in response:
        st.error(f"Error getting teams: {response['error']}")
        return []
        
    # The API already returns the details we need
    return response
    
def create_team(team_info: Dict[str, str]) -> Optional[int]:
    """Create a new team.
    
    Args:
        team_info: Dictionary with team information
        
    Returns:
        Team ID if successful, None otherwise
    """
    # Transform team_info to match API expectations
    api_team_data = {
        "name": team_info.get("team_name", ""),
        "league": team_info.get("league", ""),
        "head_coach": team_info.get("head_coach", ""),
        "assistant_coach1": team_info.get("assistant_coach1", ""),
        "assistant_coach2": team_info.get("assistant_coach2", "")
    }
    
    response = api_client.create_team(api_team_data)
    
    if "error" in response:
        st.error(f"Error creating team: {response['error']}")
        return None
        
    return response.get("id")
    
def get_team_info(team_id: int) -> Dict[str, str]:
    """Get team info.
    
    Args:
        team_id: Team ID
        
    Returns:
        Dictionary with team information
    """
    response = api_client.get_team(team_id)
    
    if "error" in response:
        st.error(f"Error getting team info: {response['error']}")
        return {
            "team_name": "",
            "league": "",
            "head_coach": "",
            "assistant_coach1": "",
            "assistant_coach2": ""
        }
        
    # Transform API response to expected format
    return {
        "team_name": response.get("name", ""),
        "league": response.get("league", ""),
        "head_coach": response.get("head_coach", ""),
        "assistant_coach1": response.get("assistant_coach1", ""),
        "assistant_coach2": response.get("assistant_coach2", "")
    }
    
def update_team(team_id: int, team_info: Dict[str, str]) -> bool:
    """Update team information.
    
    Args:
        team_id: Team ID
        team_info: Dictionary with updated team information
        
    Returns:
        True if successful, False otherwise
    """
    # Transform team_info to match API expectations
    api_team_data = {
        "name": team_info.get("team_name", ""),
        "league": team_info.get("league", ""),
        "head_coach": team_info.get("head_coach", ""),
        "assistant_coach1": team_info.get("assistant_coach1", ""),
        "assistant_coach2": team_info.get("assistant_coach2", "")
    }
    
    response = api_client.update_team(team_id, api_team_data)
    
    if "error" in response:
        st.error(f"Error updating team: {response['error']}")
        return False
        
    return True
    
def delete_team(team_id: int) -> Tuple[bool, str]:
    """Delete a team.
    
    Args:
        team_id: Team ID
        
    Returns:
        Tuple of (success, message)
    """
    # First get the team name for the success message
    team_response = api_client.get_team(team_id)
    team_name = team_response.get("name", "Unknown team") if "error" not in team_response else "Unknown team"
    
    # Delete the team
    response = api_client.delete_team(team_id)
    
    if "error" in response:
        return False, response["error"]
        
    return True, team_name
    
# Player functions
def get_roster(team_id: int) -> pd.DataFrame:
    """Get team roster as a dataframe.
    
    Args:
        team_id: Team ID
        
    Returns:
        Dataframe with player information
    """
    response = api_client.get_players(team_id)
    
    if "error" in response:
        st.error(f"Error getting roster: {response['error']}")
        return pd.DataFrame(columns=["First Name", "Last Name", "Jersey Number"])
        
    # Transform API response to expected dataframe format
    data = {
        "First Name": [],
        "Last Name": [],
        "Jersey Number": []
    }
    
    for player in response:
        data["First Name"].append(player.get("first_name", ""))
        data["Last Name"].append(player.get("last_name", ""))
        data["Jersey Number"].append(player.get("jersey_number", ""))
        
    return pd.DataFrame(data)
    
def update_roster(team_id: int, roster_df: pd.DataFrame) -> bool:
    """Update team roster from dataframe.
    
    Args:
        team_id: Team ID
        roster_df: Dataframe with player information
        
    Returns:
        True if successful, False otherwise
    """
    # This is a more complex operation that would require:
    # 1. Getting current players to determine which to update/delete
    # 2. Creating new players
    # 3. Updating existing players
    # 4. Deleting removed players
    
    # For simplicity, let's just delete all players and recreate them
    # In production, you'd want a more sophisticated approach
    
    # First, get current players
    current_players = api_client.get_players(team_id)
    
    if "error" in current_players:
        st.error(f"Error getting current roster: {current_players['error']}")
        return False
        
    # Delete all current players
    for player in current_players:
        delete_response = api_client.delete_player(player["id"])
        if "error" in delete_response:
            st.error(f"Error deleting player: {delete_response['error']}")
            return False
    
    # Create new players from dataframe
    for _, row in roster_df.iterrows():
        player_data = {
            "first_name": row["First Name"],
            "last_name": row["Last Name"],
            "jersey_number": str(row["Jersey Number"])
        }
        
        create_response = api_client.create_player(team_id, player_data)
        if "error" in create_response:
            st.error(f"Error creating player: {create_response['error']}")
            return False
    
    return True
    
# Game functions
def get_schedule(team_id: int) -> pd.DataFrame:
    """Get team schedule as a dataframe.
    
    Args:
        team_id: Team ID
        
    Returns:
        Dataframe with game information
    """
    response = api_client.get_games(team_id)
    
    if "error" in response:
        st.error(f"Error getting schedule: {response['error']}")
        return pd.DataFrame(columns=["Game #", "Date", "Time", "Opponent", "Innings"])
        
    # Transform API response to expected dataframe format
    data = {
        "Game #": [],
        "Date": [],
        "Time": [],
        "Opponent": [],
        "Innings": []
    }
    
    for game in response:
        data["Game #"].append(game.get("game_number", 0))
        data["Date"].append(game.get("date"))
        data["Time"].append(game.get("time"))
        data["Opponent"].append(game.get("opponent", ""))
        data["Innings"].append(game.get("innings", 6))
        
    df = pd.DataFrame(data)
    # Ensure Date column is datetime type
    df["Date"] = pd.to_datetime(df["Date"])
    return df
    
def update_schedule(team_id: int, schedule_df: pd.DataFrame) -> bool:
    """Update team schedule from dataframe.
    
    Args:
        team_id: Team ID
        schedule_df: Dataframe with game information
        
    Returns:
        True if successful, False otherwise
    """
    # Similar to update_roster, this would require a more complex implementation
    # We'll use a similar approach for simplicity
    
    # First, get current games
    current_games = api_client.get_games(team_id)
    
    if "error" in current_games:
        st.error(f"Error getting current schedule: {current_games['error']}")
        return False
        
    # Delete all current games
    for game in current_games:
        delete_response = api_client.delete_game(game["id"])
        if "error" in delete_response:
            st.error(f"Error deleting game: {delete_response['error']}")
            return False
    
    # Create new games from dataframe
    for _, row in schedule_df.iterrows():
        game_data = {
            "game_number": int(row["Game #"]),
            "date": row["Date"].strftime("%Y-%m-%d") if pd.notna(row["Date"]) else None,
            "time": row["Time"].strftime("%H:%M:%S") if 'Time' in row and pd.notna(row["Time"]) else None,
            "opponent": row["Opponent"],
            "innings": int(row["Innings"])
        }
        
        create_response = api_client.create_game(team_id, game_data)
        if "error" in create_response:
            st.error(f"Error creating game: {create_response['error']}")
            return False
    
    return True
    
def get_game_by_number(team_id: int, game_number: int) -> Optional[Dict[str, Any]]:
    """Get a game by its game number.
    
    Args:
        team_id: Team ID
        game_number: Game number
        
    Returns:
        Game data if found, None otherwise
    """
    # Get all games for the team
    response = api_client.get_games(team_id)
    
    if "error" in response:
        st.error(f"Error getting games: {response['error']}")
        return None
        
    # Find the game with the matching game_number
    for game in response:
        if game.get("game_number") == game_number:
            return game
            
    return None

# Initialize API client if token is in session state
if "api_token" in st.session_state and st.session_state.api_token:
    api_client.set_token(st.session_state.api_token)