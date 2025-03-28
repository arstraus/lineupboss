#!/usr/bin/env python3
"""
LineupBoss API Migration Test Script

This script tests all critical API endpoints after the migration to ensure they're working correctly
in the production environment. It requires a valid JWT token from a logged-in user.

Usage:
    python test_api_migration.py --token <JWT_TOKEN>

The token can be obtained from the browser's local storage after logging in.
"""

import argparse
import json
import time
import sys
import requests
from datetime import datetime
from urllib.parse import urljoin

# Define color codes for terminal output
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

class APITester:
    def __init__(self, base_url, token, verbose=False):
        self.base_url = base_url
        self.token = token
        self.verbose = verbose
        self.success_count = 0
        self.failure_count = 0
        self.total_tests = 0
        self.failures = []
        
        # Resources created during testing (for cleanup)
        self.created_resources = {
            'teams': [],
            'players': [],
            'games': []
        }

    def get_headers(self):
        """Get authorization headers with JWT token."""
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make an API request and validate the response."""
        url = urljoin(self.base_url, endpoint)
        self.total_tests += 1
        
        if self.verbose:
            print(f"\n{Colors.BOLD}Request:{Colors.ENDC} {method} {url}")
            if data:
                print(f"{Colors.BOLD}Data:{Colors.ENDC} {json.dumps(data, indent=2)}")
        
        # Make the request
        try:
            if method.lower() == 'get':
                response = requests.get(url, headers=self.get_headers())
            elif method.lower() == 'post':
                response = requests.post(url, headers=self.get_headers(), json=data)
            elif method.lower() == 'put':
                response = requests.put(url, headers=self.get_headers(), json=data)
            elif method.lower() == 'delete':
                response = requests.delete(url, headers=self.get_headers())
            else:
                print(f"{Colors.FAIL}❌ Unknown method: {method}{Colors.ENDC}")
                self.failure_count += 1
                return None
            
            # Print response summary
            status_color = Colors.GREEN if response.status_code == expected_status else Colors.FAIL
            status_symbol = "✅" if response.status_code == expected_status else "❌"
            
            print(f"{status_color}{status_symbol} {method.upper()} {endpoint} - {response.status_code}{Colors.ENDC}")
            
            # Handle response based on expected status
            if expected_status is not None and response.status_code != expected_status:
                self.failure_count += 1
                failure_info = {
                    'endpoint': endpoint,
                    'method': method,
                    'expected_status': expected_status,
                    'actual_status': response.status_code,
                    'response': response.text[:200] + ('...' if len(response.text) > 200 else '')
                }
                self.failures.append(failure_info)
                
                if self.verbose:
                    print(f"{Colors.FAIL}Expected status: {expected_status}, got: {response.status_code}{Colors.ENDC}")
                    print(f"{Colors.FAIL}Response: {response.text}{Colors.ENDC}")
                return None
            
            # Success case
            self.success_count += 1
            if self.verbose and response.headers.get('content-type', '').startswith('application/json'):
                try:
                    print(f"{Colors.CYAN}Response:{Colors.ENDC} {json.dumps(response.json(), indent=2)}")
                except json.JSONDecodeError:
                    print(f"{Colors.CYAN}Response:{Colors.ENDC} {response.text}")
            
            return response
            
        except requests.RequestException as e:
            self.failure_count += 1
            print(f"{Colors.FAIL}❌ {method.upper()} {endpoint} - Request error: {str(e)}{Colors.ENDC}")
            return None

    def run_test_suite(self):
        """Run the full test suite against all critical API endpoints."""
        print(f"{Colors.HEADER}{Colors.BOLD}LineupBoss API Migration Test{Colors.ENDC}")
        print(f"{Colors.BOLD}Base URL:{Colors.ENDC} {self.base_url}")
        print(f"{Colors.BOLD}Testing Date:{Colors.ENDC} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Colors.BOLD}Token:{Colors.ENDC} {self.token[:10]}...{self.token[-10:] if len(self.token) > 20 else ''}")
        print("\n" + "="*80 + "\n")

        # Run tests in sequence, grouped by functionality
        self.test_auth()
        self.test_teams()
        self.test_players()
        self.test_games()
        self.test_lineups()
        self.test_analytics()
        self.test_admin()
        
        # Cleanup created resources
        self.cleanup_resources()
        
        # Print summary
        self.print_summary()

    def test_auth(self):
        """Test authentication endpoints."""
        print(f"\n{Colors.BLUE}{Colors.BOLD}Testing Authentication Endpoints{Colors.ENDC}\n")
        
        # Test current user endpoint (already authenticated)
        self.make_request('get', '/api/auth/me')
        
        # Test token refresh
        self.make_request('post', '/api/auth/refresh')
    
    def test_teams(self):
        """Test team-related endpoints."""
        print(f"\n{Colors.BLUE}{Colors.BOLD}Testing Team Endpoints{Colors.ENDC}\n")
        
        # Get all teams
        teams_response = self.make_request('get', '/api/teams')
        
        if teams_response:
            # Create a new team
            team_data = {
                'name': f'Test Team {int(time.time())}',
                'league': 'API Test League'
            }
            create_response = self.make_request('post', '/api/teams', data=team_data, expected_status=201)
            
            if create_response and create_response.status_code == 201:
                team_id = create_response.json().get('id')
                self.created_resources['teams'].append(team_id)
                
                # Get the team by ID
                self.make_request('get', f'/api/teams/{team_id}')
                
                # Update the team
                update_data = {
                    'name': f'Updated Team {int(time.time())}',
                    'league': 'Updated Test League'
                }
                self.make_request('put', f'/api/teams/{team_id}', data=update_data)
    
    def test_players(self):
        """Test player-related endpoints."""
        print(f"\n{Colors.BLUE}{Colors.BOLD}Testing Player Endpoints{Colors.ENDC}\n")
        
        # Need at least one team
        if not self.created_resources['teams']:
            print(f"{Colors.WARNING}⚠️ No teams available for player tests, skipping{Colors.ENDC}")
            return
        
        team_id = self.created_resources['teams'][0]
        
        # Get all players for the team
        self.make_request('get', f'/api/teams/{team_id}/players')
        
        # Create a new player
        player_data = {
            'name': f'Test Player {int(time.time())}',
            'position': 'Pitcher',
            'jersey_number': '42'
        }
        create_response = self.make_request('post', f'/api/teams/{team_id}/players', data=player_data, expected_status=201)
        
        if create_response and create_response.status_code == 201:
            player_id = create_response.json().get('id')
            self.created_resources['players'].append(player_id)
            
            # Get the player by ID
            self.make_request('get', f'/api/players/{player_id}')
            
            # Update the player
            update_data = {
                'name': f'Updated Player {int(time.time())}',
                'position': 'Catcher',
                'jersey_number': '24'
            }
            self.make_request('put', f'/api/players/{player_id}', data=update_data)
    
    def test_games(self):
        """Test game-related endpoints."""
        print(f"\n{Colors.BLUE}{Colors.BOLD}Testing Game Endpoints{Colors.ENDC}\n")
        
        # Need at least one team
        if not self.created_resources['teams']:
            print(f"{Colors.WARNING}⚠️ No teams available for game tests, skipping{Colors.ENDC}")
            return
        
        team_id = self.created_resources['teams'][0]
        
        # Get all games for the team
        self.make_request('get', f'/api/teams/{team_id}/games')
        
        # Create a new game
        game_data = {
            'opponent': f'Test Opponent {int(time.time())}',
            'location': 'Test Field',
            'game_date': datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        }
        create_response = self.make_request('post', f'/api/teams/{team_id}/games', data=game_data, expected_status=201)
        
        if create_response and create_response.status_code == 201:
            game_id = create_response.json().get('id')
            self.created_resources['games'].append(game_id)
            
            # Get the game by ID
            self.make_request('get', f'/api/games/{game_id}')
            
            # Update the game
            update_data = {
                'opponent': f'Updated Opponent {int(time.time())}',
                'location': 'Updated Field',
                'game_date': datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            }
            self.make_request('put', f'/api/games/{game_id}', data=update_data)
    
    def test_lineups(self):
        """Test lineup-related endpoints."""
        print(f"\n{Colors.BLUE}{Colors.BOLD}Testing Lineup Endpoints{Colors.ENDC}\n")
        
        # Need at least one game and player
        if not self.created_resources['games'] or not self.created_resources['players']:
            print(f"{Colors.WARNING}⚠️ Not enough resources for lineup tests, skipping{Colors.ENDC}")
            return
        
        game_id = self.created_resources['games'][0]
        player_id = self.created_resources['players'][0]
        
        # Get batting order
        self.make_request('get', f'/api/games/{game_id}/batting-order')
        
        # Save batting order
        batting_order_data = {
            'order_data': [
                {'player_id': player_id, 'order': 1}
            ]
        }
        self.make_request('post', f'/api/games/{game_id}/batting-order', data=batting_order_data)
        
        # Get fielding rotations
        self.make_request('get', f'/api/games/{game_id}/fielding-rotations')
        
        # Save fielding rotation
        fielding_data = {
            'positions': [
                {'player_id': player_id, 'position': 'Pitcher'}
            ]
        }
        self.make_request('post', f'/api/games/{game_id}/fielding-rotations/1', data=fielding_data)
        
        # Get player availability
        self.make_request('get', f'/api/games/{game_id}/player-availability')
        
        # Save player availability
        availability_data = {
            'available': True
        }
        self.make_request('post', f'/api/games/{game_id}/player-availability/{player_id}', data=availability_data)
        
        # Test AI fielding rotation generation
        if player_id:
            ai_data = {
                'available_players': [player_id],
                'positions': ['Pitcher', 'Catcher', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF'],
                'innings': 3
            }
            # This might fail if the user doesn't have the AI feature
            self.make_request('post', f'/api/games/{game_id}/ai-fielding-rotation', data=ai_data, expected_status=None)
    
    def test_analytics(self):
        """Test analytics endpoints."""
        print(f"\n{Colors.BLUE}{Colors.BOLD}Testing Analytics Endpoints{Colors.ENDC}\n")
        
        # Need at least one team
        if not self.created_resources['teams']:
            print(f"{Colors.WARNING}⚠️ No teams available for analytics tests, skipping{Colors.ENDC}")
            return
        
        team_id = self.created_resources['teams'][0]
        
        # Check analytics status (try both original and v2 versions)
        self.make_request('get', '/api/analytics/status')
        
        # Get team analytics (RESTful endpoint)
        self.make_request('get', f'/api/analytics/teams/{team_id}')
        
        # Get team analytics (legacy endpoint)
        self.make_request('get', f'/api/analytics/teams/{team_id}/analytics')
        
        # Get player batting analytics (RESTful endpoint)
        self.make_request('get', f'/api/analytics/teams/{team_id}/players/batting')
        
        # Get player batting analytics (legacy endpoint)
        self.make_request('get', f'/api/analytics/teams/{team_id}/batting-analytics')
        
        # Get player fielding analytics (RESTful endpoint)
        self.make_request('get', f'/api/analytics/teams/{team_id}/players/fielding')
        
        # Get player fielding analytics (legacy endpoint)
        self.make_request('get', f'/api/analytics/teams/{team_id}/fielding-analytics')
        
        # Get debug analytics data
        self.make_request('get', f'/api/analytics/teams/{team_id}/debug')
    
    def test_admin(self):
        """Test admin endpoints."""
        print(f"\n{Colors.BLUE}{Colors.BOLD}Testing Admin Endpoints{Colors.ENDC}\n")
        
        # These will likely fail for non-admin users, so set expected_status=None
        # Get pending users
        self.make_request('get', '/api/admin/users?status=pending', expected_status=None)
        
        # Get pending count
        self.make_request('get', '/api/admin/pending-count', expected_status=None)
    
    def cleanup_resources(self):
        """Clean up resources created during testing."""
        print(f"\n{Colors.BLUE}{Colors.BOLD}Cleaning Up Test Resources{Colors.ENDC}\n")
        
        # Delete games
        for game_id in self.created_resources['games']:
            self.make_request('delete', f'/api/games/{game_id}')
        
        # Delete players
        for player_id in self.created_resources['players']:
            self.make_request('delete', f'/api/players/{player_id}')
        
        # Delete teams
        for team_id in self.created_resources['teams']:
            self.make_request('delete', f'/api/teams/{team_id}')
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*80)
        print(f"\n{Colors.BOLD}Test Summary:{Colors.ENDC}")
        print(f"Total tests: {self.total_tests}")
        print(f"{Colors.GREEN}Passed: {self.success_count}{Colors.ENDC}")
        print(f"{Colors.FAIL}Failed: {self.failure_count}{Colors.ENDC}")
        
        success_rate = (self.success_count / self.total_tests) * 100 if self.total_tests > 0 else 0
        color = Colors.GREEN if success_rate >= 90 else Colors.WARNING if success_rate >= 75 else Colors.FAIL
        print(f"{color}Success rate: {success_rate:.2f}%{Colors.ENDC}")
        
        # Print details of failures
        if self.failures:
            print(f"\n{Colors.BOLD}Failed Tests:{Colors.ENDC}")
            for i, failure in enumerate(self.failures):
                print(f"{Colors.FAIL}{i+1}. {failure['method'].upper()} {failure['endpoint']}{Colors.ENDC}")
                print(f"   Expected status: {failure['expected_status']}, got: {failure['actual_status']}")
                if failure['response']:
                    print(f"   Response: {failure['response']}")
                print("")
        
        # Conclusion
        if self.failure_count == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✅ All tests passed successfully! The API migration appears complete.{Colors.ENDC}")
        elif self.failure_count <= 3:
            print(f"\n{Colors.WARNING}{Colors.BOLD}⚠️ Most tests passed with a few failures. Check the failures and consider if they are expected.{Colors.ENDC}")
        else:
            print(f"\n{Colors.FAIL}{Colors.BOLD}❌ Multiple test failures detected. Review the API migration and fix the issues.{Colors.ENDC}")

def main():
    """Parse arguments and run the API test suite."""
    parser = argparse.ArgumentParser(description='Test LineupBoss API after migration')
    parser.add_argument('--token', required=True, help='JWT token for authentication')
    parser.add_argument('--base-url', default='https://lineupboss.app', help='Base URL for the API')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    tester = APITester(args.base_url, args.token, args.verbose)
    tester.run_test_suite()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)