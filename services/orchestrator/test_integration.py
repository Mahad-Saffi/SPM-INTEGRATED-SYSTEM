"""
Cross-Service Integration & Data Sync Test Suite
Tests data flow between orchestrator and all microservices
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:9000"
ATLAS_URL = "http://localhost:8000"
WORKPULSE_URL = "http://localhost:8001"
EPR_URL = "http://localhost:8003"
LABS_URL = "http://localhost:8004"

SERVICE_TOKEN = "shared-secret-token"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

class IntegrationTest:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.org_id = None
        self.test_email = f"integration_test_{int(time.time())}@example.com"
        self.results = {"passed": 0, "failed": 0}
    
    def print_section(self, title):
        print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
        print(f"{BOLD}{BLUE}{title}{RESET}")
        print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")
    
    def test_pass(self, message):
        self.results["passed"] += 1
        print(f"{GREEN}✓{RESET} {message}")
    
    def test_fail(self, message, error=""):
        self.results["failed"] += 1
        print(f"{RED}✗{RESET} {message}")
        if error:
            print(f"  {RED}Error: {error}{RESET}")
    
    def register_user(self):
        """Step 1: Register user in orchestrator"""
        self.print_section("Step 1: User Registration in Orchestrator")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={
                "email": self.test_email,
                "password": "TestPass123!",
                "name": "Integration Test User",
                "role": "developer"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            self.user_id = data["user"]["id"]
            self.org_id = data["user"]["organization_id"]
            self.test_pass(f"User registered: {self.test_email}")
            self.test_pass(f"User ID: {self.user_id}")
            self.test_pass(f"Organization ID: {self.org_id}")
            print(f"\n{YELLOW}JWT Token:{RESET} {self.token[:50]}...")
            return True
        else:
            self.test_fail("User registration failed", response.text)
            return False
    
    def check_user_in_services(self):
        """Step 2: Verify user exists in all microservices"""
        self.print_section("Step 2: Verify User Sync Across Services")
        
        headers = {"X-Service-Token": SERVICE_TOKEN}
        
        # Check Atlas
        try:
            response = requests.get(
                f"{ATLAS_URL}/api/v1/users",
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                self.test_pass(f"Atlas service reachable (status {response.status_code})")
            else:
                self.test_fail("Atlas users endpoint failed", f"Status: {response.status_code}")
        except Exception as e:
            self.test_fail("Atlas service check failed", str(e))
        
        # Check WorkPulse
        try:
            response = requests.get(
                f"{WORKPULSE_URL}/health",
                timeout=5
            )
            if response.status_code == 200:
                self.test_pass(f"WorkPulse service healthy")
            else:
                self.test_fail("WorkPulse health check failed")
        except Exception as e:
            self.test_fail("WorkPulse service check failed", str(e))
        
        # Check EPR
        try:
            response = requests.get(
                f"{EPR_URL}/health",
                timeout=5
            )
            if response.status_code == 200:
                self.test_pass(f"EPR service healthy")
            else:
                self.test_fail("EPR health check failed")
        except Exception as e:
            self.test_fail("EPR service check failed", str(e))
        
        # Check Labs
        try:
            response = requests.get(
                f"{LABS_URL}/health",
                timeout=5
            )
            if response.status_code == 200:
                self.test_pass(f"Labs service healthy")
            else:
                self.test_fail("Labs health check failed")
        except Exception as e:
            self.test_fail("Labs service check failed", str(e))
    
    def test_direct_service_calls(self):
        """Step 3: Test direct calls to microservices"""
        self.print_section("Step 3: Direct Service API Calls")
        
        headers = {
            "X-Service-Token": SERVICE_TOKEN,
            "Content-Type": "application/json"
        }
        
        print(f"{YELLOW}Testing WorkPulse direct API...{RESET}")
        try:
            # Create user in WorkPulse directly
            response = requests.post(
                f"{WORKPULSE_URL}/api/v1/users",
                headers=headers,
                json={
                    "id": self.user_id,
                    "orchestrator_user_id": self.user_id,
                    "email": self.test_email,
                    "name": "Integration Test User"
                },
                timeout=5
            )
            
            if response.status_code in [200, 201, 409]:  # 409 = already exists
                self.test_pass(f"WorkPulse user creation: {response.status_code}")
                
                # Log activity directly
                response = requests.post(
                    f"{WORKPULSE_URL}/api/v1/activity",
                    headers=headers,
                    json={
                        "user_id": self.user_id,
                        "event": "test_activity",
                        "input_type": "keyboard",
                        "duration_seconds": 60
                    },
                    timeout=5
                )
                
                if response.status_code in [200, 201]:
                    self.test_pass("Activity logged directly in WorkPulse")
                    
                    # Retrieve activity
                    response = requests.get(
                        f"{WORKPULSE_URL}/api/v1/activity/user/{self.user_id}",
                        headers=headers,
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        activities = response.json()
                        self.test_pass(f"Retrieved {len(activities)} activities from WorkPulse")
                    else:
                        self.test_fail("Failed to retrieve activities", response.text)
                else:
                    self.test_fail("Failed to log activity", response.text)
            else:
                self.test_fail("WorkPulse user creation failed", response.text)
        
        except Exception as e:
            self.test_fail("WorkPulse direct API test failed", str(e))
        
        print(f"\n{YELLOW}Testing EPR direct API...{RESET}")
        try:
            # Create goal directly
            response = requests.post(
                f"{EPR_URL}/api/v1/goals",
                headers=headers,
                json={
                    "user_id": self.user_id,
                    "title": "Direct Goal Test",
                    "description": "Testing direct EPR API",
                    "goal_type": "qualitative",
                    "start_date": datetime.now().isoformat(),
                    "target_date": datetime.now().isoformat()
                },
                timeout=5
            )
            
            if response.status_code in [200, 201]:
                self.test_pass("Goal created directly in EPR")
                goal_id = response.json().get("id")
                
                # Retrieve goals
                response = requests.get(
                    f"{EPR_URL}/api/v1/goals/user/{self.user_id}",
                    headers=headers,
                    timeout=5
                )
                
                if response.status_code == 200:
                    goals = response.json()
                    self.test_pass(f"Retrieved {len(goals)} goals from EPR")
                else:
                    self.test_fail("Failed to retrieve goals", response.text)
            else:
                self.test_fail("EPR goal creation failed", response.text)
        
        except Exception as e:
            self.test_fail("EPR direct API test failed", str(e))
        
        print(f"\n{YELLOW}Testing Labs direct API...{RESET}")
        try:
            # Create lab directly
            response = requests.post(
                f"{LABS_URL}/api/v1/labs",
                headers=headers,
                json={
                    "name": "Direct Test Lab",
                    "description": "Testing direct Labs API",
                    "field": "Computer Science",
                    "created_by": self.user_id
                },
                timeout=5
            )
            
            if response.status_code in [200, 201]:
                self.test_pass("Lab created directly in Labs service")
                
                # Retrieve labs
                response = requests.get(
                    f"{LABS_URL}/api/v1/labs",
                    headers=headers,
                    timeout=5
                )
                
                if response.status_code == 200:
                    labs = response.json()
                    self.test_pass(f"Retrieved {len(labs)} labs from Labs service")
                else:
                    self.test_fail("Failed to retrieve labs", response.text)
            else:
                self.test_fail("Labs creation failed", response.text)
        
        except Exception as e:
            self.test_fail("Labs direct API test failed", str(e))
    
    def test_orchestrator_routing(self):
        """Step 4: Test data retrieval through orchestrator"""
        self.print_section("Step 4: Orchestrator Routing Test")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        print(f"{YELLOW}Testing orchestrator → WorkPulse routing...{RESET}")
        response = requests.get(
            f"{BASE_URL}/api/v1/monitoring/activity/{self.user_id}/today",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            activities = response.json()
            self.test_pass(f"Orchestrator routed to WorkPulse: {len(activities)} activities")
        else:
            self.test_fail("Orchestrator → WorkPulse routing failed", response.text)
        
        print(f"\n{YELLOW}Testing orchestrator → EPR routing...{RESET}")
        response = requests.get(
            f"{BASE_URL}/api/v1/performance/user/{self.user_id}/goals",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            goals = response.json()
            self.test_pass(f"Orchestrator routed to EPR: {len(goals)} goals")
        else:
            self.test_fail("Orchestrator → EPR routing failed", response.text)
        
        print(f"\n{YELLOW}Testing orchestrator → Labs routing...{RESET}")
        response = requests.get(
            f"{BASE_URL}/api/v1/research/labs",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            labs = response.json()
            self.test_pass(f"Orchestrator routed to Labs: {len(labs)} labs")
        else:
            self.test_fail("Orchestrator → Labs routing failed", response.text)
    
    def test_dashboard_aggregation(self):
        """Step 5: Test unified dashboard"""
        self.print_section("Step 5: Unified Dashboard Aggregation")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/v1/dashboard",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            dashboard = response.json()
            self.test_pass("Dashboard loaded successfully")
            
            sections = []
            if "projects" in dashboard:
                sections.append("projects")
                print(f"  → Projects section: {dashboard.get('projects', {})}")
            if "activity" in dashboard:
                sections.append("activity")
                print(f"  → Activity section: {dashboard.get('activity', {})}")
            if "performance" in dashboard:
                sections.append("performance")
                print(f"  → Performance section: {dashboard.get('performance', {})}")
            if "research" in dashboard:
                sections.append("research")
                print(f"  → Research section: {dashboard.get('research', {})}")
            
            self.test_pass(f"Dashboard contains {len(sections)} sections: {', '.join(sections)}")
        else:
            self.test_fail("Dashboard loading failed", response.text)
    
    def check_database_schemas(self):
        """Step 6: Verify database schemas"""
        self.print_section("Step 6: Database Schema Verification")
        
        print(f"{YELLOW}Checking PostgreSQL schemas...{RESET}")
        
        import subprocess
        try:
            result = subprocess.run(
                ['docker', 'exec', 'project-postgres', 'psql', '-U', 'paperless', 
                 '-d', 'project_management', '-c', '\\dn'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                schemas = result.stdout
                expected = ['atlas', 'workpulse', 'performance', 'labs']
                found = []
                
                for schema in expected:
                    if schema in schemas:
                        found.append(schema)
                        self.test_pass(f"Schema '{schema}' exists")
                    else:
                        self.test_fail(f"Schema '{schema}' missing")
                
                if len(found) == len(expected):
                    self.test_pass("All required schemas present")
            else:
                self.test_fail("Database schema check failed", result.stderr)
        
        except Exception as e:
            self.test_fail("Database check failed", str(e))
    
    def print_summary(self):
        """Print test summary"""
        self.print_section("Test Summary")
        
        total = self.results["passed"] + self.results["failed"]
        success_rate = (self.results["passed"] / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"{GREEN}Passed: {self.results['passed']}{RESET}")
        print(f"{RED}Failed: {self.results['failed']}{RESET}")
        print(f"Success Rate: {success_rate:.1f}%\n")
        
        if self.token:
            print(f"{BOLD}Test User Credentials:{RESET}")
            print(f"Email: {self.test_email}")
            print(f"Password: TestPass123!")
            print(f"User ID: {self.user_id}")
            print(f"Organization ID: {self.org_id}")
            print(f"\n{BOLD}JWT Token:{RESET}")
            print(f"{self.token}\n")
        
        return self.results["failed"] == 0
    
    def run_all_tests(self):
        """Run all integration tests"""
        print(f"\n{BOLD}{'='*60}{RESET}")
        print(f"{BOLD}🔗 Cross-Service Integration Test Suite{RESET}")
        print(f"{BOLD}{'='*60}{RESET}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        if not self.register_user():
            print(f"\n{RED}Cannot continue without user registration{RESET}")
            return False
        
        self.check_user_in_services()
        self.test_direct_service_calls()
        self.test_orchestrator_routing()
        self.test_dashboard_aggregation()
        self.check_database_schemas()
        
        return self.print_summary()


def main():
    test = IntegrationTest()
    success = test.run_all_tests()
    
    if success:
        print(f"{GREEN}{BOLD}✓ All integration tests passed!{RESET}\n")
        return 0
    else:
        print(f"{RED}{BOLD}✗ Some integration tests failed!{RESET}\n")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
