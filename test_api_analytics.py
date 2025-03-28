#!/usr/bin/env python3
"""
LineupBoss Analytics API Test Script

This script tests all analytics endpoints after restoration.

Usage:
    python test_api_analytics.py --token <JWT_TOKEN> --base-url <URL> --team-id <TEAM_ID>

The token can be obtained from the browser's local storage after logging in.
"""

import argparse
import json
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

class AnalyticsTester:
    def __init__(self, base_url, token, team_id, verbose=False):
        self.base_url = base_url
        self.token = token
        self.team_id = team_id
        self.verbose = verbose
        self.success_count = 0
        self.failure_count = 0
        self.total_tests = 0
        self.failures = []

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

    def run_analytics_tests(self):
        """Run the analytics test suite."""
        print(f"{Colors.HEADER}{Colors.BOLD}LineupBoss Analytics API Test{Colors.ENDC}")
        print(f"{Colors.BOLD}Base URL:{Colors.ENDC} {self.base_url}")
        print(f"{Colors.BOLD}Testing Date:{Colors.ENDC} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Colors.BOLD}Team ID:{Colors.ENDC} {self.team_id}")
        print(f"{Colors.BOLD}Token:{Colors.ENDC} {self.token[:10]}...{self.token[-10:] if len(self.token) > 20 else ''}")
        print("\n" + "="*80 + "\n")

        # Run tests in sequence for all analytics endpoints
        self.test_analytics_endpoints()
        
        # Print summary
        self.print_summary()

    def test_analytics_endpoints(self):
        """Test analytics endpoints."""
        print(f"\n{Colors.BLUE}{Colors.BOLD}Testing Analytics Endpoints{Colors.ENDC}\n")
        
        # Check analytics status
        self.make_request('get', '/api/analytics/status')
        
        # Get team analytics (RESTful endpoint)
        self.make_request('get', f'/api/analytics/teams/{self.team_id}')
        
        # Get team analytics (legacy endpoint)
        self.make_request('get', f'/api/analytics/teams/{self.team_id}/analytics')
        
        # Get player batting analytics (RESTful endpoint)
        self.make_request('get', f'/api/analytics/teams/{self.team_id}/players/batting')
        
        # Get player batting analytics (legacy endpoint)
        self.make_request('get', f'/api/analytics/teams/{self.team_id}/batting-analytics')
        
        # Get player fielding analytics (RESTful endpoint)
        self.make_request('get', f'/api/analytics/teams/{self.team_id}/players/fielding')
        
        # Get player fielding analytics (legacy endpoint)
        self.make_request('get', f'/api/analytics/teams/{self.team_id}/fielding-analytics')
        
        # Get debug analytics data
        self.make_request('get', f'/api/analytics/teams/{self.team_id}/debug')
    
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
            print(f"\n{Colors.GREEN}{Colors.BOLD}✅ All analytics tests passed successfully! The analytics restoration is complete.{Colors.ENDC}")
        elif self.failure_count <= 2:
            print(f"\n{Colors.WARNING}{Colors.BOLD}⚠️ Most analytics tests passed with a few failures. Check the failures and consider if they are expected.{Colors.ENDC}")
        else:
            print(f"\n{Colors.FAIL}{Colors.BOLD}❌ Multiple analytics test failures detected. The analytics restoration is incomplete.{Colors.ENDC}")

def main():
    """Parse arguments and run the analytics test suite."""
    parser = argparse.ArgumentParser(description='Test LineupBoss Analytics API')
    parser.add_argument('--token', required=True, help='JWT token for authentication')
    parser.add_argument('--base-url', default='https://lineupboss-7fbdffdfe200.herokuapp.com', help='Base URL for the API')
    parser.add_argument('--team-id', required=True, help='Team ID to test with')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    tester = AnalyticsTester(args.base_url, args.token, args.team_id, args.verbose)
    tester.run_analytics_tests()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)