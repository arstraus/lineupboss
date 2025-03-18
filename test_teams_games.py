#!/usr/bin/env python3
import requests
import json
import sys
import os

# Base URL for API
API_URL = "http://localhost:5000"  # Change if using a different port

# Get JWT token from environment or command line
JWT_TOKEN = os.environ.get("JWT_TOKEN")
if not JWT_TOKEN and len(sys.argv) > 1:
    JWT_TOKEN = sys.argv[1]

if not JWT_TOKEN:
    print("Error: JWT token not provided. Set JWT_TOKEN environment variable or pass as first argument.")
    sys.exit(1)

# Setup headers with JWT token
headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json"
}

def print_result(response):
    print(f"Status Code: {response.status_code}")
    print(f"Response time: {response.elapsed.total_seconds()}s")
    
    try:
        data = response.json()
        print(f"Response JSON: {json.dumps(data, indent=2)}")
    except:
        print(f"Response Text: {response.text[:200]}...")

def test_teams_api():
    print("\n=== Testing Teams API ===")
    
    # Get all teams
    print("\n--- GET /api/teams ---")
    response = requests.get(f"{API_URL}/api/teams", headers=headers)
    print_result(response)
    
    # Create a new team
    print("\n--- POST /api/teams ---")
    team_data = {
        "name": "Test Team",
        "league": "Test League",
        "head_coach": "Test Coach"
    }
    response = requests.post(f"{API_URL}/api/teams", headers=headers, json=team_data)
    print_result(response)
    
    if response.status_code == 201:
        team_id = response.json().get("id")
        print(f"Created team with ID: {team_id}")
        
        # Get the specific team
        print(f"\n--- GET /api/teams/{team_id} ---")
        response = requests.get(f"{API_URL}/api/teams/{team_id}", headers=headers)
        print_result(response)
        
        return team_id
    else:
        print("Failed to create test team, skipping subsequent team tests")
        return None

def test_games_api(team_id):
    if not team_id:
        print("\nSkipping games API tests as no team was created")
        return
    
    print(f"\n=== Testing Games API for Team {team_id} ===")
    
    # Get all games for team
    print(f"\n--- GET /api/games/team/{team_id} ---")
    response = requests.get(f"{API_URL}/api/games/team/{team_id}", headers=headers)
    print_result(response)
    
    # Create a new game
    print(f"\n--- POST /api/games/team/{team_id} ---")
    game_data = {
        "game_number": 1,
        "opponent": "Test Opponent",
        "date": "2025-05-01",
        "time": "14:00",
        "innings": 6
    }
    response = requests.post(f"{API_URL}/api/games/team/{team_id}", headers=headers, json=game_data)
    print_result(response)
    
    if response.status_code == 201:
        game_id = response.json().get("id")
        print(f"Created game with ID: {game_id}")
        
        # Get the specific game
        print(f"\n--- GET /api/games/{game_id} ---")
        response = requests.get(f"{API_URL}/api/games/{game_id}", headers=headers)
        print_result(response)
    else:
        print("Failed to create test game, skipping subsequent game tests")

# Run tests
if __name__ == "__main__":
    # First check the API health
    print("Testing API health...")
    try:
        response = requests.get(f"{API_URL}/api")
        if response.status_code == 200:
            print(f"API is available at {API_URL}/api")
        else:
            print(f"API returned status code {response.status_code}")
    except Exception as e:
        print(f"Error connecting to API: {e}")
        sys.exit(1)
        
    # Test teams and games API
    team_id = test_teams_api()
    test_games_api(team_id)
    
    print("\nAPI tests completed")