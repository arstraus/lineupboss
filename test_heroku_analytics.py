#!/usr/bin/env python3
"""
Simple script to test the Heroku analytics endpoints.

Usage:
    python3 test_heroku_analytics.py
"""
import requests
import sys
import json

# Configuration
BASE_URL = "https://lineupboss-7fbdffdfe200.herokuapp.com"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0MzIwMTYxMSwianRpIjoiYzhkMTYyOGQtNDA0OS00NzZhLWFjMTktMWIyZDMyMzU4ZjNhIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3NDMyMDE2MTEsImNzcmYiOiJiNmYzNzg0ZC0yYmI3LTQyZmUtYWQ3NS05NjVkMjMzZWNmNzkiLCJleHAiOjE3NDQ0OTc2MTF9.kl3Ww8fWWpbUU9gSl8auB0unaPjGK0vZqV2qJXrmNTw"
TEAM_ID = 2

def test_endpoint(endpoint, auth=False):
    """Test an endpoint and print the result."""
    url = f"{BASE_URL}{endpoint}"
    
    headers = {}
    if auth:
        headers["Authorization"] = f"Bearer {TOKEN}"
    
    print(f"\nTesting: {url}")
    print(f"Auth: {'Yes' if auth else 'No'}")
    
    try:
        response = requests.get(url, headers=headers)
        status = response.status_code
        
        print(f"Status: {status}")
        
        if status == 200:
            try:
                data = response.json()
                print("Response:")
                print(json.dumps(data, indent=2))
                return True
            except json.JSONDecodeError:
                print("Response (not JSON):")
                print(response.text[:200])
                return False
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Request failed: {str(e)}")
        return False

# Test all analytics endpoints
print("===== TESTING ANALYTICS ENDPOINTS =====")

# Public endpoints (no auth)
test_endpoint("/api/analytics/status")
test_endpoint("/api/analytics/test")

# Authenticated endpoints
test_endpoint("/api/analytics/teams/2", auth=True)
test_endpoint("/api/analytics/teams/2/analytics", auth=True)
test_endpoint("/api/analytics/teams/2/players/batting", auth=True)
test_endpoint("/api/analytics/teams/2/batting-analytics", auth=True)
test_endpoint("/api/analytics/teams/2/players/fielding", auth=True)
test_endpoint("/api/analytics/teams/2/fielding-analytics", auth=True)
test_endpoint("/api/analytics/teams/2/debug", auth=True)

print("\nAll tests completed!")