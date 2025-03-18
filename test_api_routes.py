#!/usr/bin/env python3
"""
API Routes Testing Script for LineupBoss

This script tests all API endpoints in both standard and emergency formats
to identify which routes are working and which are failing.

Usage:
    python test_api_routes.py [--base-url URL] [--token TOKEN]

Options:
    --base-url URL    Base URL of the API (default: https://www.lineupboss.app)
    --token TOKEN     JWT token for authenticated requests (required)
"""

import requests
import json
import time
import argparse
import sys
from datetime import datetime

# Colorful output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")

def print_section(text):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.BLUE}{'-' * len(text)}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.CYAN}ℹ {text}{Colors.ENDC}")

class ApiTester:
    def __init__(self, base_url, token):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}"}
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": base_url,
            "standard_routes": {},
            "emergency_routes": {},
            "summary": {
                "total": 0,
                "success_standard": 0,
                "success_emergency": 0,
                "failed_both": 0
            }
        }
        self.log_file = f"api_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    def test_endpoint(self, endpoint, method="GET", data=None, expected_status=200):
        """Test a specific API endpoint"""
        # Standard route (with single /api prefix)
        standard_url = f"{self.base_url}/api{endpoint}"
        # Emergency route (with double /api/api prefix)
        emergency_url = f"{self.base_url}/api/api{endpoint}"
        
        standard_result = self._make_request(standard_url, method, data, expected_status)
        emergency_result = self._make_request(emergency_url, method, data, expected_status)
        
        endpoint_name = endpoint.lstrip('/')
        self.results["standard_routes"][endpoint_name] = standard_result
        self.results["emergency_routes"][endpoint_name] = emergency_result
        
        # Update summary statistics
        self.results["summary"]["total"] += 1
        if standard_result["success"]:
            self.results["summary"]["success_standard"] += 1
        if emergency_result["success"]:
            self.results["summary"]["success_emergency"] += 1
        if not (standard_result["success"] or emergency_result["success"]):
            self.results["summary"]["failed_both"] += 1
        
        # Print results
        if standard_result["success"] and emergency_result["success"]:
            print_success(f"{endpoint} - Both routes working")
        elif standard_result["success"]:
            print_warning(f"{endpoint} - Standard route working, emergency route failing")
        elif emergency_result["success"]:
            print_warning(f"{endpoint} - Emergency route working, standard route failing")
        else:
            print_error(f"{endpoint} - Both routes failing")
        
        # Add details if either failed
        if not (standard_result["success"] and emergency_result["success"]):
            if not standard_result["success"]:
                print_info(f"  Standard: {standard_result['status_code']} - {standard_result['error']}")
            if not emergency_result["success"]:
                print_info(f"  Emergency: {emergency_result['status_code']} - {emergency_result['error']}")
        
        # Add a small delay to avoid overwhelming the server
        time.sleep(0.2)
        
        return standard_result["success"] or emergency_result["success"]

    def _make_request(self, url, method, data, expected_status):
        """Helper to make an HTTP request and return the result"""
        result = {
            "url": url,
            "method": method,
            "success": False,
            "status_code": None,
            "error": None,
            "response": None
        }
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            else:
                result["error"] = f"Unsupported method: {method}"
                return result
            
            result["status_code"] = response.status_code
            
            if response.status_code == expected_status:
                result["success"] = True
                try:
                    result["response"] = response.json()
                except:
                    result["response"] = "Non-JSON response"
            else:
                try:
                    error_data = response.json()
                    result["error"] = json.dumps(error_data)
                except:
                    result["error"] = response.text[:100] + "..." if len(response.text) > 100 else response.text
        except Exception as e:
            result["error"] = str(e)
        
        return result

    def save_results(self):
        """Save test results to a JSON file"""
        with open(self.log_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print_success(f"Results saved to {self.log_file}")

    def run_all_tests(self):
        """Run all API endpoint tests"""
        print_header("LineupBoss API Routes Test")
        print_info(f"Base URL: {self.base_url}")
        print_info(f"Testing started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print_info("Testing all standard and emergency routes\n")

        # Authentication endpoints
        print_section("Authentication Endpoints")
        # Skip login test since we already have a token
        #self.test_endpoint("/auth/login", method="POST", data={"email": "test@example.com", "password": "password"})
        self.test_endpoint("/auth/me")
        
        # User endpoints
        print_section("User Endpoints")
        self.test_endpoint("/user/profile")
        self.test_endpoint("/user/subscription")
        
        # Teams endpoints
        print_section("Teams Endpoints")
        self.test_endpoint("/teams")
        
        # Try to extract a team ID to use for further tests
        team_id = self._get_team_id()
        
        if team_id:
            self.test_endpoint(f"/teams/{team_id}")
            
            # Players endpoints
            print_section("Players Endpoints")
            self.test_endpoint(f"/teams/{team_id}/players")
            
            player_id = self._get_player_id(team_id)
            if player_id:
                self.test_endpoint(f"/players/{player_id}")
            
            # Games endpoints
            print_section("Games Endpoints")
            self.test_endpoint(f"/teams/{team_id}/games")
            
            game_id = self._get_game_id(team_id)
            if game_id:
                self.test_endpoint(f"/games/{game_id}")
                self.test_endpoint(f"/games/{game_id}/batting-order")
                self.test_endpoint(f"/games/{game_id}/fielding-rotations")
                self.test_endpoint(f"/games/{game_id}/player-availability")
        
        # Admin endpoints
        print_section("Admin Endpoints")
        self.test_endpoint("/admin/pending-count")
        self.test_endpoint("/admin/users?status=pending")
        
        # Print summary
        self._print_summary()
        
        # Save results
        self.save_results()

    def _get_team_id(self):
        """Try to extract a team ID from the teams list response"""
        standard_url = f"{self.base_url}/api/teams"
        emergency_url = f"{self.base_url}/api/api/teams"
        
        for url in [standard_url, emergency_url]:
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    teams = response.json()
                    if teams and len(teams) > 0 and 'id' in teams[0]:
                        team_id = teams[0]['id']
                        print_info(f"Using team ID: {team_id} for further tests")
                        return team_id
            except:
                pass
        
        print_warning("No team ID found for further tests")
        return None

    def _get_player_id(self, team_id):
        """Try to extract a player ID from the players list response"""
        standard_url = f"{self.base_url}/api/teams/{team_id}/players"
        emergency_url = f"{self.base_url}/api/api/teams/{team_id}/players"
        
        for url in [standard_url, emergency_url]:
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    players = response.json()
                    if players and len(players) > 0 and 'id' in players[0]:
                        player_id = players[0]['id']
                        print_info(f"Using player ID: {player_id} for further tests")
                        return player_id
            except:
                pass
        
        print_warning("No player ID found for further tests")
        return None

    def _get_game_id(self, team_id):
        """Try to extract a game ID from the games list response"""
        standard_url = f"{self.base_url}/api/teams/{team_id}/games"
        emergency_url = f"{self.base_url}/api/api/teams/{team_id}/games"
        
        for url in [standard_url, emergency_url]:
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    games = response.json()
                    if games and len(games) > 0 and 'id' in games[0]:
                        game_id = games[0]['id']
                        print_info(f"Using game ID: {game_id} for further tests")
                        return game_id
            except:
                pass
        
        print_warning("No game ID found for further tests")
        return None

    def _print_summary(self):
        """Print a summary of the test results"""
        total = self.results["summary"]["total"]
        standard_ok = self.results["summary"]["success_standard"]
        emergency_ok = self.results["summary"]["success_emergency"]
        both_failed = self.results["summary"]["failed_both"]
        
        print_section("Test Summary")
        print_info(f"Total endpoints tested: {total}")
        print_info(f"Standard routes working: {standard_ok}/{total} ({standard_ok/total*100:.1f}%)")
        print_info(f"Emergency routes working: {emergency_ok}/{total} ({emergency_ok/total*100:.1f}%)")
        print_info(f"Both routes failing: {both_failed}/{total} ({both_failed/total*100:.1f}%)")
        
        if standard_ok == total:
            print_success("All standard routes are working!")
        elif emergency_ok == total:
            print_warning("All emergency routes are working, but some standard routes are failing")
        elif both_failed == 0:
            print_warning("For each endpoint, at least one route is working")
        else:
            print_error(f"{both_failed} endpoints are completely inaccessible")

def main():
    parser = argparse.ArgumentParser(description="Test LineupBoss API routes")
    parser.add_argument("--base-url", default="https://www.lineupboss.app", 
                        help="Base URL for the API")
    parser.add_argument("--token", required=True,
                        help="JWT token for authenticated requests")
    
    args = parser.parse_args()
    
    tester = ApiTester(args.base_url, args.token)
    tester.run_all_tests()

if __name__ == "__main__":
    main()