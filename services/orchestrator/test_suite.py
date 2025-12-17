"""
Comprehensive Test Suite for Orchestrator API
Tests all endpoints across all microservices
"""
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:9000"
HEADERS = {"Content-Type": "application/json"}

# ANSI color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.tests = []
    
    def add_pass(self, name: str, details: str = ""):
        self.passed += 1
        self.tests.append({"name": name, "status": "PASS", "details": details})
        print(f"{GREEN}✓{RESET} {name}")
        if details:
            print(f"  {details}")
    
    def add_fail(self, name: str, error: str):
        self.failed += 1
        self.tests.append({"name": name, "status": "FAIL", "error": error})
        print(f"{RED}✗{RESET} {name}")
        print(f"  {RED}Error: {error}{RESET}")
    
    def add_skip(self, name: str, reason: str):
        self.skipped += 1
        self.tests.append({"name": name, "status": "SKIP", "reason": reason})
        print(f"{YELLOW}○{RESET} {name} (skipped: {reason})")
    
    def summary(self):
        total = self.passed + self.failed + self.skipped
        print(f"\n{BOLD}{'='*60}{RESET}")
        print(f"{BOLD}Test Summary{RESET}")
        print(f"{'='*60}")
        print(f"Total Tests: {total}")
        print(f"{GREEN}Passed: {self.passed}{RESET}")
        print(f"{RED}Failed: {self.failed}{RESET}")
        print(f"{YELLOW}Skipped: {self.skipped}{RESET}")
        print(f"Success Rate: {(self.passed/total*100) if total > 0 else 0:.1f}%")
        print(f"{'='*60}\n")

class OrchestratorTestSuite:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.org_id: Optional[str] = None
        self.results = TestResult()
        self.test_email = f"test_{int(time.time())}@example.com"
        self.test_password = "TestPassword123!"
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, auth: bool = False) -> tuple:
        """Make HTTP request and return (success, response_data, error)"""
        url = f"{self.base_url}{endpoint}"
        headers = HEADERS.copy()
        
        if auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return False, None, f"Unknown method: {method}"
            
            if response.status_code in [200, 201]:
                return True, response.json(), None
            else:
                return False, response.json() if response.text else None, f"Status {response.status_code}"
        
        except requests.exceptions.Timeout:
            return False, None, "Request timeout"
        except requests.exceptions.ConnectionError:
            return False, None, "Connection error - service may be down"
        except Exception as e:
            return False, None, str(e)
    
    def test_health(self):
        """Test 1: Health Check"""
        print(f"\n{BOLD}{BLUE}=== 1. Health & Service Status ==={RESET}\n")
        
        success, data, error = self.make_request("GET", "/api/v1/health")
        if success and data.get("orchestrator") == "healthy":
            services = data.get("services", {})
            healthy_count = sum(1 for s in services.values() if s.get("status") == "healthy")
            self.results.add_pass(
                "Health Check",
                f"Orchestrator healthy, {healthy_count}/{len(services)} services healthy"
            )
            
            # Check individual services
            for name, info in services.items():
                if info.get("status") == "healthy":
                    self.results.add_pass(f"  └─ {name.upper()} service", info.get("url"))
                else:
                    self.results.add_fail(f"  └─ {name.upper()} service", f"Status: {info.get('status')}")
        else:
            self.results.add_fail("Health Check", error or "Orchestrator not healthy")
    
    def test_registration(self):
        """Test 2: User Registration"""
        print(f"\n{BOLD}{BLUE}=== 2. Authentication - Registration ==={RESET}\n")
        
        data = {
            "email": self.test_email,
            "password": self.test_password,
            "name": "Test User",
            "role": "developer"
        }
        
        success, response, error = self.make_request("POST", "/api/v1/auth/register", data)
        if success and response.get("access_token"):
            self.token = response["access_token"]
            self.user_id = response.get("user_id")
            self.results.add_pass(
                "User Registration",
                f"User: {self.test_email}, ID: {self.user_id}"
            )
        else:
            self.results.add_fail("User Registration", error or "No token received")
    
    def test_login(self):
        """Test 3: User Login"""
        print(f"\n{BOLD}{BLUE}=== 3. Authentication - Login ==={RESET}\n")
        
        data = {
            "email": self.test_email,
            "password": self.test_password
        }
        
        success, response, error = self.make_request("POST", "/api/v1/auth/login", data)
        if success and response.get("access_token"):
            self.token = response["access_token"]
            self.results.add_pass("User Login", f"Token received for {self.test_email}")
        else:
            self.results.add_fail("User Login", error or "No token received")
    
    def test_current_user(self):
        """Test 4: Get Current User"""
        print(f"\n{BOLD}{BLUE}=== 4. Get Current User Info ==={RESET}\n")
        
        if not self.token:
            self.results.add_skip("Get Current User", "No auth token available")
            return
        
        success, response, error = self.make_request("GET", "/api/v1/auth/me", auth=True)
        if success:
            self.results.add_pass(
                "Get Current User",
                f"Name: {response.get('name')}, Email: {response.get('email')}"
            )
            if not self.user_id:
                self.user_id = response.get("id")
        else:
            self.results.add_fail("Get Current User", error or "Failed to get user info")
    
    def test_organization(self):
        """Test 5: Create Organization"""
        print(f"\n{BOLD}{BLUE}=== 5. Organization Management ==={RESET}\n")
        
        if not self.token:
            self.results.add_skip("Create Organization", "No auth token available")
            return
        
        data = {
            "name": "Test Organization",
            "description": "Organization created by test suite"
        }
        
        success, response, error = self.make_request("POST", "/api/v1/auth/organizations", data, auth=True)
        if success:
            self.org_id = response.get("id")
            self.results.add_pass(
                "Create Organization",
                f"Name: {response.get('name')}, ID: {self.org_id}"
            )
        else:
            self.results.add_fail("Create Organization", error or "Failed to create org")
    
    def test_projects(self):
        """Test 6: Projects (Atlas Service)"""
        print(f"\n{BOLD}{BLUE}=== 6. Projects (Atlas Service) ==={RESET}\n")
        
        if not self.token:
            self.results.add_skip("Get Projects", "No auth token available")
            return
        
        success, response, error = self.make_request("GET", "/api/v1/projects/", auth=True)
        if success:
            projects = response if isinstance(response, list) else []
            self.results.add_pass(
                "Get Projects List",
                f"Found {len(projects)} project(s)"
            )
        else:
            self.results.add_fail("Get Projects List", error or "Failed to get projects")
    
    def test_monitoring(self):
        """Test 7: Activity Monitoring (WorkPulse Service)"""
        print(f"\n{BOLD}{BLUE}=== 7. Activity Monitoring (WorkPulse) ==={RESET}\n")
        
        if not self.token or not self.user_id:
            self.results.add_skip("Activity Monitoring", "No auth token or user ID")
            return
        
        # Test activity log
        data = {
            "event": "test_activity",
            "input_type": "keyboard",
            "duration_seconds": 10.5
        }
        
        success, response, error = self.make_request("POST", "/api/v1/monitoring/activity/log", data, auth=True)
        if success:
            self.results.add_pass("Log Activity", "Activity logged successfully")
        else:
            self.results.add_fail("Log Activity", error or "Failed to log activity")
        
        # Test get today's activity
        success, response, error = self.make_request("GET", f"/api/v1/monitoring/activity/{self.user_id}/today", auth=True)
        if success:
            activities = response if isinstance(response, list) else []
            self.results.add_pass(
                "Get Today's Activity",
                f"Found {len(activities)} activity record(s)"
            )
        else:
            self.results.add_fail("Get Today's Activity", error or "Failed to get activities")
        
        # Test productivity stats
        success, response, error = self.make_request("GET", f"/api/v1/monitoring/stats/{self.user_id}/productivity", auth=True)
        if success:
            self.results.add_pass("Get Productivity Stats", "Stats retrieved successfully")
        else:
            self.results.add_fail("Get Productivity Stats", error or "Failed to get stats")
    
    def test_performance(self):
        """Test 8: Performance Management (EPR Service)"""
        print(f"\n{BOLD}{BLUE}=== 8. Performance Management (EPR) ==={RESET}\n")
        
        if not self.token or not self.user_id:
            self.results.add_skip("Performance Management", "No auth token or user ID")
            return
        
        # Test get goals
        success, response, error = self.make_request("GET", f"/api/v1/performance/user/{self.user_id}/goals", auth=True)
        if success:
            goals = response if isinstance(response, list) else []
            self.results.add_pass("Get User Goals", f"Found {len(goals)} goal(s)")
        else:
            self.results.add_fail("Get User Goals", error or "Failed to get goals")
        
        # Test create goal
        data = {
            "title": "Complete Test Suite",
            "description": "Successfully run all integration tests",
            "goal_type": "qualitative",
            "start_date": datetime.now().isoformat(),
            "target_date": datetime.now().isoformat()
        }
        
        success, response, error = self.make_request("POST", "/api/v1/performance/goals", data, auth=True)
        if success:
            self.results.add_pass("Create Goal", f"Goal created: {data['title']}")
        else:
            self.results.add_fail("Create Goal", error or "Failed to create goal")
        
        # Test get skills
        success, response, error = self.make_request("GET", f"/api/v1/performance/user/{self.user_id}/skills", auth=True)
        if success:
            skills = response if isinstance(response, list) else []
            self.results.add_pass("Get User Skills", f"Found {len(skills)} skill(s)")
        else:
            self.results.add_fail("Get User Skills", error or "Failed to get skills")
        
        # Test get reviews
        success, response, error = self.make_request("GET", f"/api/v1/performance/user/{self.user_id}/reviews", auth=True)
        if success:
            reviews = response if isinstance(response, list) else []
            self.results.add_pass("Get Performance Reviews", f"Found {len(reviews)} review(s)")
        else:
            self.results.add_fail("Get Performance Reviews", error or "Failed to get reviews")
    
    def test_research(self):
        """Test 9: Research Labs (Labs Service)"""
        print(f"\n{BOLD}{BLUE}=== 9. Research Labs (Labs Service) ==={RESET}\n")
        
        if not self.token:
            self.results.add_skip("Research Labs", "No auth token available")
            return
        
        # Test get labs
        success, response, error = self.make_request("GET", "/api/v1/research/labs", auth=True)
        if success:
            labs = response if isinstance(response, list) else []
            self.results.add_pass("Get Labs List", f"Found {len(labs)} lab(s)")
        else:
            self.results.add_fail("Get Labs List", error or "Failed to get labs")
        
        # Test create lab
        data = {
            "name": "Test Lab",
            "description": "Lab created by test suite",
            "field": "Computer Science"
        }
        
        success, response, error = self.make_request("POST", "/api/v1/research/labs", data, auth=True)
        if success:
            lab_id = response.get("id")
            self.results.add_pass("Create Lab", f"Lab created: {data['name']}, ID: {lab_id}")
        else:
            self.results.add_fail("Create Lab", error or "Failed to create lab")
        
        # Test get researchers
        success, response, error = self.make_request("GET", "/api/v1/research/researchers", auth=True)
        if success:
            researchers = response if isinstance(response, list) else []
            self.results.add_pass("Get Researchers", f"Found {len(researchers)} researcher(s)")
        else:
            self.results.add_fail("Get Researchers", error or "Failed to get researchers")
        
        # Test get collaborations
        success, response, error = self.make_request("GET", "/api/v1/research/collaborations", auth=True)
        if success:
            collabs = response if isinstance(response, list) else []
            self.results.add_pass("Get Collaborations", f"Found {len(collabs)} collaboration(s)")
        else:
            self.results.add_fail("Get Collaborations", error or "Failed to get collaborations")
    
    def test_dashboard(self):
        """Test 10: Unified Dashboard"""
        print(f"\n{BOLD}{BLUE}=== 10. Unified Dashboard ==={RESET}\n")
        
        if not self.token:
            self.results.add_skip("Unified Dashboard", "No auth token available")
            return
        
        success, response, error = self.make_request("GET", "/api/v1/dashboard", auth=True)
        if success:
            sections = []
            if response.get("projects"): sections.append("projects")
            if response.get("activity"): sections.append("activity")
            if response.get("performance"): sections.append("performance")
            if response.get("research"): sections.append("research")
            
            self.results.add_pass(
                "Unified Dashboard",
                f"Dashboard loaded with sections: {', '.join(sections)}"
            )
        else:
            self.results.add_fail("Unified Dashboard", error or "Failed to load dashboard")
    
    def test_team_features(self):
        """Test 11: Team Features"""
        print(f"\n{BOLD}{BLUE}=== 11. Team Features ==={RESET}\n")
        
        if not self.token or not self.org_id:
            self.results.add_skip("Team Features", "No auth token or org ID")
            return
        
        # Test team activity
        success, response, error = self.make_request("GET", f"/api/v1/monitoring/team/{self.org_id}", auth=True)
        if success:
            activities = response if isinstance(response, list) else []
            self.results.add_pass("Get Team Activity", f"Found {len(activities)} activity record(s)")
        else:
            self.results.add_fail("Get Team Activity", error or "Failed to get team activity")
        
        # Test team performance
        success, response, error = self.make_request("GET", f"/api/v1/performance/team/{self.org_id}/performance", auth=True)
        if success:
            self.results.add_pass("Get Team Performance", "Team performance retrieved")
        else:
            self.results.add_fail("Get Team Performance", error or "Failed to get team performance")
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print(f"\n{BOLD}{'='*60}{RESET}")
        print(f"{BOLD}🧪 Orchestrator Integration Test Suite{RESET}")
        print(f"{BOLD}{'='*60}{RESET}")
        print(f"Base URL: {self.base_url}")
        print(f"Test User: {self.test_email}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        # Run all tests
        self.test_health()
        self.test_registration()
        self.test_login()
        self.test_current_user()
        self.test_organization()
        self.test_projects()
        self.test_monitoring()
        self.test_performance()
        self.test_research()
        self.test_dashboard()
        self.test_team_features()
        
        # Print summary
        self.results.summary()
        
        # Print token info for manual testing
        if self.token:
            print(f"{BOLD}Authentication Token (for manual testing):{RESET}")
            print(f"{self.token}\n")
        
        return self.results.failed == 0


def main():
    """Main entry point"""
    print("\nStarting Orchestrator Test Suite...\n")
    
    suite = OrchestratorTestSuite()
    success = suite.run_all_tests()
    
    if success:
        print(f"{GREEN}{BOLD}✓ All tests passed!{RESET}\n")
        return 0
    else:
        print(f"{RED}{BOLD}✗ Some tests failed!{RESET}\n")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
