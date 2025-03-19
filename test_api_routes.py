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
                          (auth, system, user, teams, players, games, lineup, admin, docs)
    --test-credentials     File with test credentials (email:password) for login/register tests
    --verbose              Show more detailed output for each test
    --continue-on-error    Continue testing even if dependencies (like team_id) are missing
    --output-file FILE     Path to save test results (default: auto-generated filename)
    --check-performance    Report slow endpoints (>500ms response time)
"""

import requests
import json
import time
import argparse
import sys
import os
import uuid
from datetime import datetime, date

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

def print_debug(text, verbose=False):
    if verbose:
        print(f"  {text}")

class ApiTester:
    def __init__(self, base_url, token, dry_run=True, endpoint_group=None, test_credentials=None, 
                verbose=False, continue_on_error=False, output_file=None, check_performance=False):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}"}
        self.dry_run = dry_run
        self.endpoint_group = endpoint_group
        self.test_credentials = test_credentials
        self.verbose = verbose
        self.continue_on_error = continue_on_error
        self.check_performance = check_performance
        self.test_email = None
        self.test_password = None
        self.slow_threshold_ms = 500  # Threshold for slow response warnings
        
        # Test data storage
        self.test_resources = {
            "team_id": None,
            "player_id": None,
            "game_id": None,
            "inning": 1,
            "created_resources": []  # Track resources we create for cleanup
        }
        
        # Load test credentials if provided
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
            },
            "performance": {
                "slow_endpoints": [],
                "average_response_time": 0,
                "total_time": 0
            }
        }
        
        # Set output file
        if output_file:
            self.log_file = output_file
        else:
            self.log_file = f"api_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    def should_test_group(self, group):
        """Check if a specific endpoint group should be tested"""
        if not self.endpoint_group:
            return True
        return group == self.endpoint_group

    def test_endpoint(self, endpoint, method="GET", data=None, expected_status=200, skip_if_dry_run=False, 
                     group=None, description=None, cleanup_resource=False):
        """Test a specific API endpoint"""
        # Skip if the endpoint's group doesn't match the requested group
        if group and not self.should_test_group(group):
            return None
            
        # Skip data-modifying operations in dry-run mode if requested
        if skip_if_dry_run and self.dry_run and method in ["POST", "PUT", "DELETE", "PATCH"]:
            print_skipped(f"{method} {endpoint}" + (f" - {description}" if description else ""))
            self.results["summary"]["skipped"] += 1
            return None
        
        endpoint_desc = f"{method} {endpoint}" + (f" - {description}" if description else "")
            
        # Standard route (with single /api prefix)
        standard_url = f"{self.base_url}/api{endpoint}"
        # Emergency route (with double /api/api prefix)
        emergency_url = f"{self.base_url}/api/api{endpoint}"
        
        start_time = time.time()
        standard_result = self._make_request(standard_url, method, data, expected_status)
        emergency_result = self._make_request(emergency_url, method, data, expected_status)
        end_time = time.time()
        
        # Calculate response time
        response_time_ms = (end_time - start_time) * 500  # Average time per request in milliseconds
        
        endpoint_name = f"{method}:{endpoint.lstrip('/')}"
        self.results["standard_routes"][endpoint_name] = standard_result
        self.results["emergency_routes"][endpoint_name] = emergency_result
        
        # Add performance data
        standard_result["response_time_ms"] = response_time_ms
        emergency_result["response_time_ms"] = response_time_ms
        
        # Track performance metrics
        self.results["performance"]["total_time"] += response_time_ms
        if response_time_ms > self.slow_threshold_ms and self.check_performance:
            self.results["performance"]["slow_endpoints"].append({
                "endpoint": endpoint_name,
                "response_time_ms": response_time_ms
            })
            print_warning(f"Slow response: {response_time_ms:.1f}ms for {endpoint_desc}")
        
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
            print_success(endpoint_desc + " - Both routes working")
        elif standard_result["success"]:
            print_warning(endpoint_desc + " - Standard route working, emergency route failing")
        elif emergency_result["success"]:
            print_warning(endpoint_desc + " - Emergency route working, standard route failing")
        else:
            print_error(endpoint_desc + " - Both routes failing")
        
        # Add details if either failed or in verbose mode
        if self.verbose or not (standard_result["success"] and emergency_result["success"]):
            if not standard_result["success"] or self.verbose:
                print_debug(f"  Standard: {standard_result['status_code']} - {standard_result['error']}", True)
            if not emergency_result["success"] or self.verbose:
                print_debug(f"  Emergency: {emergency_result['status_code']} - {emergency_result['error']}", True)
        
        # If this created a resource we need to track for cleanup
        if cleanup_resource and method == "POST" and (standard_result["success"] or emergency_result["success"]):
            result = standard_result if standard_result["success"] else emergency_result
            if result["response"] and "id" in result["response"]:
                resource_id = result["response"]["id"]
                resource_type = group or endpoint.split("/")[1]
                self.test_resources["created_resources"].append({
                    "type": resource_type,
                    "id": resource_id,
                    "endpoint": endpoint,
                    "method": method
                })
                print_debug(f"  Created {resource_type} with ID {resource_id} for cleanup", self.verbose)
                
                # Store IDs of main resources for other tests
                if resource_type == "teams":
                    self.test_resources["team_id"] = resource_id
                elif resource_type == "players":
                    self.test_resources["player_id"] = resource_id
                elif resource_type == "games":
                    self.test_resources["game_id"] = resource_id
        
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
        # Calculate performance metrics before saving
        if self.results["summary"]["total"] > 0:
            self.results["performance"]["average_response_time"] = \
                self.results["performance"]["total_time"] / self.results["summary"]["total"]
        
        with open(self.log_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print_success(f"Results saved to {self.log_file}")

    def run_all_tests(self):
        """Run all API endpoint tests"""
        start_time = time.time()
        print_header("LineupBoss API Routes Test")
        print_info(f"Base URL: {self.base_url}")
        print_info(f"Testing started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print_info(f"Dry run mode: {self.dry_run}")
        if self.endpoint_group:
            print_info(f"Testing only {self.endpoint_group} endpoints")
        print_info("Testing all standard and emergency routes\n")

        # System endpoints
        if self.should_test_group("system"):
            print_section("System Endpoints")
            self.test_endpoint("/", group="system")
            self.test_endpoint("/test-jwt", group="system")
            self.test_endpoint("/test-db", group="system")
            self.test_endpoint("/health", group="system")

        # Documentation endpoints
        if self.should_test_group("docs"):
            print_section("Documentation Endpoints")
            self.test_endpoint("/docs/", group="docs")
            self.test_endpoint("/docs/swagger.json", group="docs")

        # Authentication endpoints
        if self.should_test_group("auth"):
            print_section("Authentication Endpoints")
            
            # Test register if credentials are provided (but only in live mode)
            if self.test_email and self.test_password and not self.dry_run:
                # Create a unique test email to avoid conflicts
                test_register_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
                print_info(f"Testing register with {test_register_email}")
                self.test_endpoint("/auth/register", method="POST", 
                                data={
                                    "email": test_register_email, 
                                    "password": "TestPassword123!",
                                    "first_name": "API", 
                                    "last_name": "Tester"
                                }, 
                                skip_if_dry_run=True,
                                group="auth",
                                description="Register new user")
            
            # Test login with provided credentials
            if self.test_email and self.test_password:
                print_info(f"Testing login with {self.test_email}")
                self.test_endpoint("/auth/login", method="POST", 
                                data={"email": self.test_email, "password": self.test_password}, 
                                group="auth",
                                description="Login existing user")
            else:
                print_info("Skipping login test (no test credentials provided)")
            
            self.test_endpoint("/auth/me", group="auth", description="Get current user info")
            self.test_endpoint("/auth/refresh", method="POST", data={}, group="auth", description="Refresh token")

        # User endpoints
        if self.should_test_group("user"):
            print_section("User Endpoints")
            
            # GET operations
            self.test_endpoint("/user/profile", group="user", description="Get user profile")
            self.test_endpoint("/user/subscription", group="user", description="Get subscription info")
            self.test_endpoint("/user/test", group="user", description="Test endpoint")
            
            # Test profile update with dry run flag
            self.test_endpoint("/user/profile", method="PUT", 
                            data={"first_name": "Test", "last_name": "User"}, 
                            skip_if_dry_run=True, group="user", description="Update profile")
            
            # Test password update with dry run flag (never actually executed)
            self.test_endpoint("/user/password", method="PUT", 
                            data={"current_password": "oldpassword", "new_password": "newpassword"}, 
                            skip_if_dry_run=True, group="user", description="Update password (normal)",
                            expected_status=200)
                            
            # Test password update with emergency route pattern
            self.test_endpoint("/api/user/password", method="PUT", 
                            data={"current_password": "oldpassword", "new_password": "newpassword"}, 
                            skip_if_dry_run=True, group="user", description="Update password (emergency)",
                            expected_status=200)

        # Teams endpoints
        if self.should_test_group("teams"):
            print_section("Teams Endpoints")
            
            # GET operations
            self.test_endpoint("/teams", group="teams", description="List all teams")
            
            # Create a test team
            team_created = self.test_endpoint("/teams", method="POST", 
                         data={
                             "name": f"Test Team {uuid.uuid4().hex[:6]}", 
                             "league": "Test League",
                             "head_coach": "Coach Smith",
                             "assistant_coach1": "Assistant Johnson",
                             "assistant_coach2": "Assistant Williams"
                         }, 
                         skip_if_dry_run=True, group="teams", description="Create team",
                         cleanup_resource=True)
            
            # If we can't create a team, try to find an existing one
            if not team_created or not self.test_resources["team_id"]:
                existing_team_id = self._get_team_id()
                if existing_team_id:
                    self.test_resources["team_id"] = existing_team_id
            
            # Team operations requiring a team ID
            if self.test_resources["team_id"]:
                team_id = self.test_resources["team_id"]
                self.test_endpoint(f"/teams/{team_id}", group="teams", description="Get team details")
                
                # Test team update
                self.test_endpoint(f"/teams/{team_id}", method="PUT", 
                                data={"name": f"Updated Team {uuid.uuid4().hex[:6]}"}, 
                                skip_if_dry_run=True, group="teams", description="Update team")
            else:
                print_warning("No team ID available for team detail/update/delete tests")
                if not self.continue_on_error:
                    print_error("Cannot continue without a team_id. Use --continue-on-error to force continuation.")
                    return

        # Players endpoints
        if self.should_test_group("players"):
            print_section("Players Endpoints")
            
            # Ensure we have a team_id
            team_id = self.test_resources["team_id"]
            if not team_id:
                team_id = self._get_team_id()
                self.test_resources["team_id"] = team_id
            
            if team_id:
                # GET operations with both route patterns
                self.test_endpoint(f"/teams/{team_id}/players", group="players", description="List players (nested)")
                self.test_endpoint(f"/players/team/{team_id}", group="players", description="List players (legacy)")
                
                # Create a test player
                player_created = self.test_endpoint(f"/teams/{team_id}/players", method="POST", 
                             data={
                                 "first_name": "Test", 
                                 "last_name": f"Player {uuid.uuid4().hex[:6]}", 
                                 "jersey_number": str(uuid.uuid4().int % 100)
                             }, 
                             skip_if_dry_run=True, group="players", description="Create player (nested)",
                             cleanup_resource=True)
                
                # Also test legacy route for player creation
                legacy_player_created = self.test_endpoint(f"/players/team/{team_id}", method="POST", 
                             data={
                                 "first_name": "Legacy", 
                                 "last_name": f"Player {uuid.uuid4().hex[:6]}", 
                                 "jersey_number": str(uuid.uuid4().int % 100 + 100)
                             }, 
                             skip_if_dry_run=True, group="players", description="Create player (legacy)",
                             cleanup_resource=True)
                
                # If we can't create a player, try to find an existing one
                if not self.test_resources["player_id"]:
                    existing_player_id = self._get_player_id(team_id)
                    if existing_player_id:
                        self.test_resources["player_id"] = existing_player_id
                
                # Player operations requiring a player ID
                if self.test_resources["player_id"]:
                    player_id = self.test_resources["player_id"]
                    self.test_endpoint(f"/players/{player_id}", group="players", description="Get player details")
                    
                    # Test player update
                    self.test_endpoint(f"/players/{player_id}", method="PUT", 
                                    data={
                                        "first_name": "Updated", 
                                        "last_name": f"Player {uuid.uuid4().hex[:6]}",
                                        "jersey_number": str(uuid.uuid4().int % 100 + 200)
                                    }, 
                                    skip_if_dry_run=True, group="players", description="Update player")
                else:
                    print_warning("No player ID available for player detail/update/delete tests")
                    if not self.continue_on_error:
                        print_error("Cannot continue without a player_id. Use --continue-on-error to force continuation.")
                        return
            else:
                print_warning("No team ID available for player tests")
                if not self.continue_on_error:
                    print_error("Cannot continue without a team_id. Use --continue-on-error to force continuation.")
                    return

        # Games endpoints
        if self.should_test_group("games"):
            print_section("Games Endpoints")
            
            # Ensure we have a team_id
            team_id = self.test_resources["team_id"]
            if not team_id:
                team_id = self._get_team_id()
                self.test_resources["team_id"] = team_id
            
            if team_id:
                # GET operations with both route patterns
                self.test_endpoint(f"/teams/{team_id}/games", group="games", description="List games (nested)")
                self.test_endpoint(f"/games/team/{team_id}", group="games", description="List games (legacy)")
                
                # Generate a game date in the future
                game_date = (datetime.now().date().replace(year=datetime.now().year + 1)).isoformat()
                
                # Create a test game with legacy route
                game_created = self.test_endpoint(f"/games/team/{team_id}", method="POST", 
                             data={
                                 "game_number": int(uuid.uuid4().int % 100), 
                                 "opponent": f"Test Opponent {uuid.uuid4().hex[:6]}", 
                                 "date": game_date, 
                                 "time": "14:00", 
                                 "innings": 6
                             }, 
                             skip_if_dry_run=True, group="games", description="Create game (legacy)",
                             cleanup_resource=True)
                
                # Create a test game with nested route
                nested_game_created = self.test_endpoint(f"/teams/{team_id}/games", method="POST", 
                             data={
                                 "game_number": int(uuid.uuid4().int % 100 + 100), 
                                 "opponent": f"Nested Opponent {uuid.uuid4().hex[:6]}", 
                                 "date": game_date, 
                                 "time": "15:00", 
                                 "innings": 6
                             }, 
                             skip_if_dry_run=True, group="games", description="Create game (nested)",
                             cleanup_resource=True)
                
                # If we can't create a game, try to find an existing one
                if not self.test_resources["game_id"]:
                    existing_game_id = self._get_game_id(team_id)
                    if existing_game_id:
                        self.test_resources["game_id"] = existing_game_id
                
                # Game operations requiring a game ID
                if self.test_resources["game_id"]:
                    game_id = self.test_resources["game_id"]
                    self.test_endpoint(f"/games/{game_id}", group="games", description="Get game details")
                    
                    # Test game update
                    self.test_endpoint(f"/games/{game_id}", method="PUT", 
                                    data={
                                        "opponent": f"Updated Opponent {uuid.uuid4().hex[:6]}",
                                        "innings": 7
                                    }, 
                                    skip_if_dry_run=True, group="games", description="Update game")
                else:
                    print_warning("No game ID available for game detail/update/delete tests")
                    if not self.continue_on_error:
                        print_error("Cannot continue without a game_id. Use --continue-on-error to force continuation.")
                        return
            else:
                print_warning("No team ID available for game tests")
                if not self.continue_on_error:
                    print_error("Cannot continue without a team_id. Use --continue-on-error to force continuation.")
                    return

        # Lineup endpoints
        if self.should_test_group("lineup"):
            print_section("Lineup Endpoints")
            
            # Ensure we have required IDs
            team_id = self.test_resources["team_id"]
            game_id = self.test_resources["game_id"]
            player_id = self.test_resources["player_id"]
            
            if not team_id:
                team_id = self._get_team_id()
                self.test_resources["team_id"] = team_id
            
            if not game_id and team_id:
                game_id = self._get_game_id(team_id)
                self.test_resources["game_id"] = game_id
                
            if not player_id and team_id:
                player_id = self._get_player_id(team_id)
                self.test_resources["player_id"] = player_id
            
            if game_id:
                # Test batting order endpoints
                self.test_endpoint(f"/games/{game_id}/batting-order", group="lineup", description="Get batting order")
                
                # Create/update batting order
                self.test_endpoint(f"/games/{game_id}/batting-order", method="POST", 
                             data={"order_data": ["1", "2", "3"]}, 
                             skip_if_dry_run=True, group="lineup", description="Create batting order")
                             
                self.test_endpoint(f"/games/{game_id}/batting-order", method="PUT", 
                             data={"order_data": ["3", "2", "1"]}, 
                             skip_if_dry_run=True, group="lineup", description="Update batting order")
                
                # Test fielding rotation endpoints
                self.test_endpoint(f"/games/{game_id}/fielding-rotations", group="lineup", description="List fielding rotations")
                self.test_endpoint(f"/games/{game_id}/fielding-rotations/1", group="lineup", description="Get fielding rotation for inning 1")
                
                # Create/update fielding rotation
                self.test_endpoint(f"/games/{game_id}/fielding-rotations/1", method="POST", 
                             data={"positions": {"Pitcher": "1", "Catcher": "2", "1B": "3"}}, 
                             skip_if_dry_run=True, group="lineup", description="Create fielding rotation")
                             
                self.test_endpoint(f"/games/{game_id}/fielding-rotations/1", method="PUT", 
                             data={"positions": {"Pitcher": "3", "Catcher": "1", "1B": "2"}}, 
                             skip_if_dry_run=True, group="lineup", description="Update fielding rotation")
                
                # Test player availability endpoints
                self.test_endpoint(f"/games/{game_id}/player-availability", group="lineup", description="List player availability")
                
                if player_id:
                    self.test_endpoint(f"/games/{game_id}/player-availability/{player_id}", group="lineup", description="Get player availability")
                    
                    # Create/update player availability
                    self.test_endpoint(f"/games/{game_id}/player-availability/{player_id}", method="POST", 
                                 data={"available": True, "can_play_catcher": False}, 
                                 skip_if_dry_run=True, group="lineup", description="Create player availability")
                                 
                    self.test_endpoint(f"/games/{game_id}/player-availability/{player_id}", method="PUT", 
                                 data={"available": False, "can_play_catcher": True}, 
                                 skip_if_dry_run=True, group="lineup", description="Update player availability")
                
                # Batch player availability endpoint
                self.test_endpoint(f"/games/{game_id}/player-availability/batch", method="POST", 
                             data=[{"player_id": player_id or 1, "available": True, "can_play_catcher": False}], 
                             skip_if_dry_run=True, group="lineup", description="Batch update player availability")
                
                # AI fielding rotation endpoint
                self.test_endpoint(f"/games/{game_id}/ai-fielding-rotation", method="POST", 
                             data={"team_id": team_id or 1, "game_id": game_id}, 
                             skip_if_dry_run=True, group="lineup", description="Generate AI fielding rotation")
            else:
                print_warning("No game ID available for lineup tests")
                if not self.continue_on_error:
                    print_error("Cannot continue without a game_id. Use --continue-on-error to force continuation.")
                    return

        # Admin endpoints
        if self.should_test_group("admin"):
            print_section("Admin Endpoints")
            
            # GET operations
            self.test_endpoint("/admin/pending-count", group="admin", description="Get pending approval count")
            self.test_endpoint("/admin/users?status=pending", group="admin", description="List pending users")
            self.test_endpoint("/admin/users", group="admin", description="List all users")
            
            # Skip admin actions in dry run mode as they affect real users
            user_id = 1  # Example user ID
            self.test_endpoint(f"/admin/users/{user_id}/approve", method="POST", 
                         skip_if_dry_run=True, group="admin", description="Approve user")
                         
            self.test_endpoint(f"/admin/users/{user_id}/reject", method="POST", 
                         skip_if_dry_run=True, group="admin", description="Reject user")
                         
            self.test_endpoint(f"/admin/users/{user_id}/role", method="PUT", 
                         data={"role": "user"}, 
                         skip_if_dry_run=True, group="admin", description="Update user role")
                         
            self.test_endpoint(f"/admin/users/{user_id}", method="DELETE", 
                         skip_if_dry_run=True, group="admin", description="Delete user")

        # Cleanup resources created during testing
        self._cleanup_test_resources()

        # Print summary
        self._print_summary()
        
        # Save results
        self.save_results()

    def _cleanup_test_resources(self):
        """Clean up test resources created during the test run"""
        if self.dry_run or not self.test_resources["created_resources"]:
            return
        
        print_section("Cleaning up test resources")
        
        # Reverse the list to delete in reverse order of creation (children before parents)
        for resource in reversed(self.test_resources["created_resources"]):
            resource_type = resource["type"]
            resource_id = resource["id"]
            
            # Determine the delete endpoint
            if resource_type == "teams":
                endpoint = f"/teams/{resource_id}"
            elif resource_type == "players":
                endpoint = f"/players/{resource_id}"
            elif resource_type == "games":
                endpoint = f"/games/{resource_id}"
            else:
                continue  # Skip if we don't know how to delete this resource
                
            print_info(f"Deleting {resource_type} with ID {resource_id}")
            standard_url = f"{self.base_url}/api{endpoint}"
            emergency_url = f"{self.base_url}/api/api{endpoint}"
            
            # Try standard route first, then emergency
            try:
                response = requests.delete(standard_url, headers=self.headers, timeout=10)
                if response.status_code in [200, 204]:
                    print_success(f"Deleted {resource_type} {resource_id} via standard route")
                    continue
            except:
                pass
                
            # Try emergency route if standard failed
            try:
                response = requests.delete(emergency_url, headers=self.headers, timeout=10)
                if response.status_code in [200, 204]:
                    print_success(f"Deleted {resource_type} {resource_id} via emergency route")
                    continue
            except:
                pass
                
            print_error(f"Failed to delete {resource_type} {resource_id}")

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
        # First try the nested route
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
        # First try the nested route
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
        
        # Calculate average response time
        if total > 0:
            avg_response_time = self.results["performance"]["total_time"] / total
            self.results["performance"]["average_response_time"] = avg_response_time
        else:
            avg_response_time = 0
        
        print_section("Test Summary")
        print_info(f"Total endpoints tested: {total}")
        print_info(f"Skipped tests: {skipped}")
        print_info(f"Standard routes working: {standard_ok}/{total} ({standard_ok/total*100:.1f}% if total > 0)" if total > 0 else f"Standard routes working: {standard_ok}/{total} (0.0%)")
        print_info(f"Emergency routes working: {emergency_ok}/{total} ({emergency_ok/total*100:.1f}% if total > 0)" if total > 0 else f"Emergency routes working: {emergency_ok}/{total} (0.0%)")
        print_info(f"Both routes failing: {both_failed}/{total} ({both_failed/total*100:.1f}% if total > 0)" if total > 0 else f"Both routes failing: {both_failed}/{total} (0.0%)")
        print_info(f"Only emergency route working: {emergency_only}/{total} ({emergency_only/total*100:.1f}% if total > 0)" if total > 0 else f"Only emergency route working: {emergency_only}/{total} (0.0%)")
        print_info(f"Only standard route working: {standard_only}/{total} ({standard_only/total*100:.1f}% if total > 0)" if total > 0 else f"Only standard route working: {standard_only}/{total} (0.0%)")
        print_info(f"Average response time: {avg_response_time:.1f}ms")
        
        if self.check_performance:
            slow_count = len(self.results["performance"]["slow_endpoints"])
            if slow_count > 0:
                print_warning(f"Found {slow_count} slow endpoints (>500ms)")
                for idx, endpoint in enumerate(self.results["performance"]["slow_endpoints"][:5]):  # Show top 5
                    print_warning(f"  {idx+1}. {endpoint['endpoint']}: {endpoint['response_time_ms']:.1f}ms")
                if slow_count > 5:
                    print_warning(f"  ...and {slow_count - 5} more")
            else:
                print_success("No slow endpoints detected")
            
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

        # How many endpoints need migration from emergency to standard
        if emergency_only > 0:
            print_section("Route Migration Recommendations")
            print_warning(f"{emergency_only} endpoints need migration from emergency to standard routes")
            print_info("These endpoints are only accessible via emergency routes (/api/api/...)")
            print_info("Frontend components using these endpoints should be updated to use standard routes")

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
                       choices=["auth", "system", "user", "teams", "players", "games", "lineup", "admin", "docs"],
                       help="Test only a specific group of endpoints")
    parser.add_argument("--test-credentials", 
                       help="File with test credentials (email:password) for login/register tests")
    parser.add_argument("--verbose", action="store_true", default=False,
                       help="Show more detailed output for each test")
    parser.add_argument("--continue-on-error", action="store_true", default=False,
                       help="Continue testing even if dependencies (like team_id) are missing")
    parser.add_argument("--output-file", 
                       help="Path to save test results (default: auto-generated filename)")
    parser.add_argument("--check-performance", action="store_true", default=False,
                       help="Report slow endpoints (>500ms response time)")
    
    args = parser.parse_args()
    
    # Override dry-run if live-data is specified
    dry_run = not args.live_data if args.live_data else args.dry_run
    
    tester = ApiTester(
        args.base_url, 
        args.token, 
        dry_run=dry_run, 
        endpoint_group=args.endpoint_group,
        test_credentials=args.test_credentials,
        verbose=args.verbose,
        continue_on_error=args.continue_on_error,
        output_file=args.output_file,
        check_performance=args.check_performance
    )
    tester.run_all_tests()

if __name__ == "__main__":
    main()