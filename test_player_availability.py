#!/usr/bin/env python3
import requests
import json

def test_player_availability_batch():
    """Test the player availability batch endpoint with detailed debug information"""
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0MjMyMDc5NywianRpIjoiYzA5MmQzNDEtNmEyYy00NTc1LTg0ODgtM2IzNzBlM2RhNTAyIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3NDIzMjA3OTcsImV4cCI6MTc0MzYxNjc5N30.m-uJ0LkqvMQPD9BC4DbceypDTH9xci9UdmrUSjYgesY"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test parameters
    game_id = 15  # Use the game ID from the logs
    
    # First, get existing player availability to see what format it returns
    get_url = f"https://www.lineupboss.app/api/api/games/{game_id}/player-availability"
    print(f"Getting current player availability: {get_url}")
    get_response = requests.get(get_url, headers=headers)
    
    if get_response.status_code == 200:
        print("GET Success! Current player availability:")
        current_data = get_response.json()
        print(json.dumps(current_data[:3], indent=2))  # Just print the first 3 entries to keep the output manageable
        
        # Create an update payload based on the existing data
        update_data = []
        for entry in current_data:
            update_data.append({
                "player_id": entry["player_id"],
                "available": True,  # Always make available for the test
                "can_play_catcher": entry.get("can_play_catcher", False)  # Preserve existing value or set default
            })
            
        # Print the exact payload we're sending
        print("\nUpdate payload (first 3 entries):")
        print(json.dumps(update_data[:3], indent=2))
        
        # Send the update
        post_url = f"https://www.lineupboss.app/api/api/games/{game_id}/player-availability/batch"
        print(f"\nPOSTing updated availability: {post_url}")
        post_response = requests.post(post_url, headers=headers, json=update_data)
        
        print(f"POST Status code: {post_response.status_code}")
        
        try:
            result = post_response.json()
            print("POST Response:")
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error parsing response: {e}")
            print("Raw response:")
            print(post_response.text)
    else:
        print(f"GET failed with status {get_response.status_code}")
        try:
            print(get_response.json())
        except:
            print(get_response.text)

if __name__ == "__main__":
    test_player_availability_batch()