#!/usr/bin/env python3
"""
API Routes Testing Script for LineupBoss

This script tests all API endpoints in both standard and emergency formats
to identify which routes are working and which are failing.

Usage:
    python test_api_routes.py [--base-url URL] [--token TOKEN] [--dry-run] [--endpoint-group GROUP]

Options:
    --base-url URL         Base URL of the API (default: https://www.lineupboss.app)
    --token TOKEN          JWT token for authenticated requests (required)
    --dry-run              Skip data-modifying operations (POST/PUT/DELETE) that would change data
    --live-data            Actually execute data-modifying operations (use with caution!)
    --endpoint-group GROUP Test only a specific group of endpoints: 
                          (auth, system, user, teams, players, games, lineup, admin)
    --test-credentials     File with test credentials (email:password) for login/register tests
"""

import requests
import json
import time
import argparse
import sys
import os
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

def print_skipped(text):
    print(f"{Colors.CYAN}⏩ {text} (SKIPPED){Colors.ENDC}")

class ApiTester:
    def __init__(self, base_url, token, dry_run=True, endpoint_group=None, test_credentials=None):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}"}
        self.dry_run = dry_run
        self.endpoint_group = endpoint_group
        self.test_credentials = test_credentials
        self.test_email = None
        self.test_password = None
        
        if test_credentials:
            try:
                with open(test_credentials, 'r') as f:
                    creds = f.read().strip()
                    if ':' in creds:
                        self.test_email, self.test_password = creds.split(':', 1)
                        print_info(f"Loaded test credentials for {self.test_email}")
            except Exception as e:
                print_warning(f"Could not load test credentials: {str(e)}")
        
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": base_url,
            "standard_routes": {},
            "emergency_routes": {},
            "summary": {
                "total": 0,
                "success_standard": 0,
                "success_emergency": 0,
                "failed_both": 0,
                "emergency_only": 0,
                "standard_only": 0,
                "skipped": 0
            }
        }
        self.log_file = f"api_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    def should_test_group(self, group):
        """Check if a specific endpoint group should be tested"""
        if not self.endpoint_group:
            return True
        return group == self.endpoint_group

    def test_endpoint(self, endpoint, method="GET", data=None, expected_status=200, skip_if_dry_run=False, group=None):
        """Test a specific API endpoint"""
        # Skip if the endpoint's group doesn't match the requested group
        if group and not self.should_test_group(group):
            return None
            
        # Skip data-modifying operations in dry-run mode if requested
        if skip_if_dry_run and self.dry_run and method in ["POST", "PUT", "DELETE", "PATCH"]:
            print_skipped(f"{method} {endpoint}")
            self.results["summary"]["skipped"] += 1
            return None
            
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
        if not standard_result["success"] and emergency_result["success"]:
            self.results["summary"]["emergency_only"] += 1
        if standard_result["success"] and not emergency_result["success"]:
            self.results["summary"]["standard_only"] += 1
        if not (standard_result["success"] or emergency_result["success"]):
            self.results["summary"]["failed_both"] += 1
        
        # Print results
        if standard_result["success"] and emergency_result["success"]:
            print_success(f"{method} {endpoint} - Both routes working")
        elif standard_result["success"]:
            print_warning(f"{method} {endpoint} - Standard route working, emergency route failing")
        elif emergency_result["success"]:
            print_warning(f"{method} {endpoint} - Emergency route working, standard route failing")
        else:
            print_error(f"{method} {endpoint} - Both routes failing")
        
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
            elif method == "PUT":
                response = requests.put(url, headers=self.headers, json=data, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers, timeout=10)
            elif method == "PATCH":
                response = requests.patch(url, headers=self.headers, json=data, timeout=10)
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
        print_info(f"Dry run mode: {self.dry_run}")
        if self.endpoint_group:
            print_info(f"Testing only {self.endpoint_group} endpoints")
        print_info("Testing all standard and emergency routes\n")

        # Authentication endpoints
        if self.should_test_group("auth"):
            print_section("Authentication Endpoints")
            
            # Test login/register if credentials are provided
            if self.test_email and self.test_password:
                print_info(f"Testing login with {self.test_email}")
                self.test_endpoint("/auth/login", method="POST", 
                                data={"email": self.test_email, "password": self.test_password}, 
                                group="auth")
                
                # Don't actually register the test user as that could create duplicate accounts
                print_info("Skipping register test to avoid duplicate accounts")
            else:
                print_info("Skipping login/register tests (no test credentials provided)")
            
            self.test_endpoint("/auth/me", group="auth")
            self.test_endpoint("/auth/refresh", method="POST", data={}, group="auth")

        # System endpoints
        if self.should_test_group("system"):
            print_section("System Endpoints")
            self.test_endpoint("/", group="system")
            self.test_endpoint("/test-jwt", group="system")
            self.test_endpoint("/test-db", group="system")
            self.test_endpoint("/health", group="system")

        # User endpoints
        if self.should_test_group("user"):
            print_section("User Endpoints")
            self.test_endpoint("/user/profile", group="user")
            self.test_endpoint("/user/subscription", group="user")
            self.test_endpoint("/user/test", group="user")  # Test endpoint
            
            # Test profile update with dry run flag
            self.test_endpoint("/user/profile", method="PUT", 
                            data={"first_name": "Test", "last_name": "User"}, 
                            skip_if_dry_run=True, group="user")
            
            # Test password update with dry run flag (never actually executed)
            self.test_endpoint("/user/password", method="PUT", 
                            data={"current_password": "oldpassword", "new_password": "newpassword"}, 
                            skip_if_dry_run=True, group="user")

        # Teams endpoints
        if self.should_test_group("teams"):
            print_section("Teams Endpoints")
            self.test_endpoint("/teams", group="teams")
            
            # Test team creation with dry run flag
            self.test_endpoint("/teams", method="POST", 
                            data={"name": "Test Team", "league": "Test League"}, 
                            skip_if_dry_run=True, group="teams")
            
            # Try to extract a team ID to use for further tests
            team_id = self._get_team_id()
            
            if team_id:
                self.test_endpoint(f"/teams/{team_id}", group="teams")
                
                # Test team update and delete with dry run flag
                self.test_endpoint(f"/teams/{team_id}", method="PUT", 
                                data={"name": "Updated Team"}, 
                                skip_if_dry_run=True, group="teams")
                                
                self.test_endpoint(f"/teams/{team_id}", method="DELETE", 
                                skip_if_dry_run=True, group="teams")

        # Players endpoints
        if self.should_test_group("players"):
            print_section("Players Endpoints")
            
            # Get team ID if we don't have one yet
            team_id = self._get_team_id() if 'team_id' not in locals() or not team_id else team_id
            
            if team_id:
                # Test both player route patterns
                self.test_endpoint(f"/teams/{team_id}/players", group="players")
                self.test_endpoint(f"/players/team/{team_id}", group="players")
                
                # Test player creation with dry run flag
                self.test_endpoint(f"/teams/{team_id}/players", method="POST", 
                                data={"first_name": "Test", "last_name": "Player", "jersey_number": "99"}, 
                                skip_if_dry_run=True, group="players")
                
                # Also test legacy route for player creation
                self.test_endpoint(f"/players/team/{team_id}", method="POST", 
                                data={"first_name": "Test", "last_name": "Legacy", "jersey_number": "98"}, 
                                skip_if_dry_run=True, group="players")
                
                player_id = self._get_player_id(team_id)
                if player_id:
                    self.test_endpoint(f"/players/{player_id}", group="players")
                    
                    # Test player update and delete with dry run flag
                    self.test_endpoint(f"/players/{player_id}", method="PUT", 
                                    data={"first_name": "Updated", "last_name": "Player"}, 
                                    skip_if_dry_run=True, group="players")
                    
                    self.test_endpoint(f"/players/{player_id}", method="DELETE", 
                                    skip_if_dry_run=True, group="players")

        # Games endpoints
        if self.should_test_group("games"):
            print_section("Games Endpoints")
            
            # Get team ID if we don't have one yet
            team_id = self._get_team_id() if 'team_id' not in locals() or not team_id else team_id
            
            if team_id:
                # Test both game route patterns
                self.test_endpoint(f"/teams/{team_id}/games", group="games")
                self.test_endpoint(f"/games/team/{team_id}", group="games")
                
                # Test game creation with dry run flag
                self.test_endpoint(f"/games/team/{team_id}", method="POST", 
                                data={
                                    "game_number": 1, 
                                    "opponent": "Test Opponent", 
                                    "date": "2025-06-01", 
                                    "time": "14:00", 
                                    "innings": 6
                                }, 
                                skip_if_dry_run=True, group="games")
                
                # Also test nested route for game creation
                self.test_endpoint(f"/teams/{team_id}/games", method="POST", 
                                data={
                                    "game_number": 2, 
                                    "opponent": "Test Opponent 2", 
                                    "date": "2025-06-02", 
                                    "time": "15:00", 
                                    "innings": 6
                                }, 
                                skip_if_dry_run=True, group="games")
                
                game_id = self._get_game_id(team_id)
                if game_id:
                    self.test_endpoint(f"/games/{game_id}", group="games")
                    
                    # Test game update and delete with dry run flag
                    self.test_endpoint(f"/games/{game_id}", method="PUT", 
                                    data={"opponent": "Updated Opponent"}, 
                                    skip_if_dry_run=True, group="games")
                    
                    self.test_endpoint(f"/games/{game_id}", method="DELETE", 
                                    skip_if_dry_run=True, group="games")

        # Lineup endpoints
        if self.should_test_group("lineup"):
            print_section("Lineup Endpoints")
            
            # Get team ID and game ID if we don't have them yet
            team_id = self._get_team_id() if 'team_id' not in locals() or not team_id else team_id
            game_id = self._get_game_id(team_id) if team_id else None
            
            if team_id and game_id:
                player_id = self._get_player_id(team_id)
                
                # Batting order endpoints
                self.test_endpoint(f"/games/{game_id}/batting-order", group="lineup")
                self.test_endpoint(f"/games/{game_id}/batting-order", method="POST", 
                                data={"order_data": ["Player1", "Player2"]}, 
                                skip_if_dry_run=True, group="lineup")
                self.test_endpoint(f"/games/{game_id}/batting-order", method="PUT", 
                                data={"order_data": ["Player2", "Player1"]}, 
                                skip_if_dry_run=True, group="lineup")
                
                # Fielding rotation endpoints
                self.test_endpoint(f"/games/{game_id}/fielding-rotations", group="lineup")
                self.test_endpoint(f"/games/{game_id}/fielding-rotations/1", group="lineup")
                self.test_endpoint(f"/games/{game_id}/fielding-rotations/1", method="POST", 
                                data={"positions": {"Pitcher": "Player1", "Catcher": "Player2"}}, 
                                skip_if_dry_run=True, group="lineup")
                self.test_endpoint(f"/games/{game_id}/fielding-rotations/1", method="PUT", 
                                data={"positions": {"Pitcher": "Player2", "Catcher": "Player1"}}, 
                                skip_if_dry_run=True, group="lineup")
                
                # Player availability endpoints
                self.test_endpoint(f"/games/{game_id}/player-availability", group="lineup")
                
                if player_id:
                    self.test_endpoint(f"/games/{game_id}/player-availability/{player_id}", group="lineup")
                    self.test_endpoint(f"/games/{game_id}/player-availability/{player_id}", method="POST", 
                                    data={"available": True, "can_play_catcher": False}, 
                                    skip_if_dry_run=True, group="lineup")
                    self.test_endpoint(f"/games/{game_id}/player-availability/{player_id}", method="PUT", 
                                    data={"available": False, "can_play_catcher": True}, 
                                    skip_if_dry_run=True, group="lineup")
                
                # Batch player availability endpoint
                self.test_endpoint(f"/games/{game_id}/player-availability/batch", method="POST", 
                                data=[{"player_id": 1, "available": True}], 
                                skip_if_dry_run=True, group="lineup")
                
                # AI fielding rotation endpoint
                self.test_endpoint(f"/games/{game_id}/ai-fielding-rotation", method="POST", 
                                data={"team_id": team_id, "game_id": game_id}, 
                                group="lineup")

        # Admin endpoints
        if self.should_test_group("admin"):
            print_section("Admin Endpoints")
            self.test_endpoint("/admin/pending-count", group="admin")
            self.test_endpoint("/admin/users?status=pending", group="admin")
            self.test_endpoint("/admin/users", group="admin")
            
            # Test user management endpoints with dry run flag
            self.test_endpoint("/admin/users/1/approve", method="POST", 
                            skip_if_dry_run=True, group="admin")
            self.test_endpoint("/admin/users/1/reject", method="POST", 
                            skip_if_dry_run=True, group="admin")
            self.test_endpoint("/admin/users/1/role", method="PUT", 
                            data={"role": "user"}, 
                            skip_if_dry_run=True, group="admin")
            self.test_endpoint("/admin/users/1", method="DELETE", 
                            skip_if_dry_run=True, group="admin")

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
        
        # Try the legacy route if the nested route didn't work
        standard_url = f"{self.base_url}/api/players/team/{team_id}"
        emergency_url = f"{self.base_url}/api/api/players/team/{team_id}"
        
        for url in [standard_url, emergency_url]:
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    players = response.json()
                    if players and len(players) > 0 and 'id' in players[0]:
                        player_id = players[0]['id']
                        print_info(f"Using player ID: {player_id} for further tests (from legacy route)")
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
        
        # Try the legacy route if the nested route didn't work
        standard_url = f"{self.base_url}/api/games/team/{team_id}"
        emergency_url = f"{self.base_url}/api/api/games/team/{team_id}"
        
        for url in [standard_url, emergency_url]:
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    games = response.json()
                    if games and len(games) > 0 and 'id' in games[0]:
                        game_id = games[0]['id']
                        print_info(f"Using game ID: {game_id} for further tests (from legacy route)")
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
        emergency_only = self.results["summary"]["emergency_only"]
        standard_only = self.results["summary"]["standard_only"]
        skipped = self.results["summary"]["skipped"]
        
        print_section("Test Summary")
        print_info(f"Total endpoints tested: {total}")
        print_info(f"Skipped tests: {skipped}")
        print_info(f"Standard routes working: {standard_ok}/{total} ({standard_ok/total*100:.1f}%)")
        print_info(f"Emergency routes working: {emergency_ok}/{total} ({emergency_ok/total*100:.1f}%)")
        print_info(f"Both routes failing: {both_failed}/{total} ({both_failed/total*100:.1f}%)")
        print_info(f"Only emergency route working: {emergency_only}/{total} ({emergency_only/total*100:.1f}%)")
        print_info(f"Only standard route working: {standard_only}/{total} ({standard_only/total*100:.1f}%)")
        
        if emergency_only > 0:
            print_warning(f"{emergency_only} endpoints are ONLY accessible via emergency routes (/api/api/...)")
            print_warning("These should be prioritized for frontend updates to use standard routes")
            
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
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Skip data-modifying operations (POST/PUT/DELETE) (default)")
    parser.add_argument("--live-data", action="store_true", default=False,
                        help="Actually execute data-modifying operations (use with caution!)")
    parser.add_argument("--endpoint-group", 
                        choices=["auth", "system", "user", "teams", "players", "games", "lineup", "admin"],
                        help="Test only a specific group of endpoints")
    parser.add_argument("--test-credentials", 
                        help="File with test credentials (email:password) for login/register tests")
    
    args = parser.parse_args()
    
    # Override dry-run if live-data is specified
    dry_run = not args.live_data if args.live_data else args.dry_run
    
    tester = ApiTester(
        args.base_url, 
        args.token, 
        dry_run=dry_run, 
        endpoint_group=args.endpoint_group,
        test_credentials=args.test_credentials
    )
    tester.run_all_tests()

if __name__ == "__main__":
    main()