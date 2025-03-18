#!/usr/bin/env python3
import requests
import json
import time

def create_player_availability(token, game_id, player_id):
    """Create a player availability record using the POST method"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Create with POST method
    url = f"https://www.lineupboss.app/api/games/{game_id}/player-availability/{player_id}"
    data = {
        "available": True,
        "can_play_catcher": False
    }
    
    print(f"Creating availability record: {url}")
    response = requests.post(url, headers=headers, json=data)
    print(f"POST Status code: {response.status_code}")
    
    try:
        result = response.json()
        print("POST Response data:")
        print(json.dumps(result, indent=2))
        return response.status_code == 200 or response.status_code == 201
    except:
        print("Raw POST response:")
        print(response.text)
        return False

def test_player_availability():
    """Test the player availability endpoint with detailed error reporting"""
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0MjMyMDc5NywianRpIjoiYzA5MmQzNDEtNmEyYy00NTc1LTg0ODgtM2IzNzBlM2RhNTAyIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3NDIzMjA3OTcsImV4cCI6MTc0MzYxNjc5N30.m-uJ0LkqvMQPD9BC4DbceypDTH9xci9UdmrUSjYgesY"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test parameters
    game_id = 11
    player_id = 15
    
    # First create the record
    success = create_player_availability(token, game_id, player_id)
    
    if success:
        print("\nCreation successful, now testing GET...\n")
    else:
        print("\nCreation failed, still testing GET...\n")
        
    # Small delay to ensure database operations complete
    time.sleep(1)
    
    # Now try to get the record
    url = f"https://www.lineupboss.app/api/games/{game_id}/player-availability/{player_id}"
    print(f"Testing GET: {url}")
    
    response = requests.get(url, headers=headers)
    print(f"GET Status code: {response.status_code}")
    
    # Try to parse as JSON
    try:
        data = response.json()
        print("GET Response data:")
        print(json.dumps(data, indent=2))
    except:
        print("Raw GET response:")
        print(response.text)

if __name__ == "__main__":
    test_player_availability()