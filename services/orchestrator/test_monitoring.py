"""
Enhanced Monitoring & Feature Test Suite
Tests real-world workflows across all microservices
"""
import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:9000"
HEADERS = {"Content-Type": "application/json"}

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

class MonitoringTestSuite:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.user_id = None
        self.org_id = None
        self.test_email = f"monitoring_test_{int(time.time())}@example.com"
        self.test_password = "TestPass123!"
        self.created_items = {
            "projects": [],
            "goals": [],
            "labs": [],
            "activities": []
        }
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, auth: bool = False):
        """Make HTTP request"""
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
            
            if response.status_code in [200, 201]:
                return True, response.json(), None
            else:
                return False, response.json() if response.text else None, f"Status {response.status_code}"
        except Exception as e:
            return False, None, str(e)
    
    def setup(self):
        """Setup: Register and login"""
        print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
        print(f"{BOLD}{CYAN}🚀 Setup: Creating Test User{RESET}")
        print(f"{CYAN}{'='*60}{RESET}\n")
        
        # Register
        data = {
            "email": self.test_email,
            "password": self.test_password,
            "name": "Monitoring Test User",
            "role": "developer"
        }
        
        success, response, error = self.make_request("POST", "/api/v1/auth/register", data)
        if success:
            self.token = response["access_token"]
            self.user_id = response["user"]["id"]
            print(f"{GREEN}✓{RESET} User registered: {self.test_email}")
            print(f"{GREEN}✓{RESET} User ID: {self.user_id}")
        else:
            print(f"{RED}✗{RESET} Registration failed: {error}")
            return False
        
        # Create organization
        org_data = {"name": "Monitoring Test Org", "description": "Testing organization"}
        success, response, error = self.make_request("POST", "/api/v1/auth/organizations", org_data, auth=True)
        if success:
            self.org_id = response["id"]
            print(f"{GREEN}✓{RESET} Organization created: {self.org_id}\n")
        
        return True
    
    def test_activity_monitoring(self):
        """Test comprehensive activity monitoring"""
        print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
        print(f"{BOLD}{BLUE}📊 Test 1: Activity Monitoring (WorkPulse){RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")
        
        # Log multiple activities
        activities = [
            {"event": "coding", "input_type": "keyboard", "duration_seconds": 1800, "application": "VSCode"},
            {"event": "active", "input_type": "mouse", "duration_seconds": 600, "application": "Chrome"},
            {"event": "active", "input_type": "keyboard", "duration_seconds": 900, "application": "Terminal"},
            {"event": "idle", "input_type": "system", "duration_seconds": 300, "application": None},
            {"event": "active", "input_type": "keyboard", "duration_seconds": 1200, "application": "VSCode"},
        ]
        
        print(f"{CYAN}Logging 5 activity events...{RESET}")
        for i, activity in enumerate(activities, 1):
            success, response, error = self.make_request("POST", "/api/v1/monitoring/activity/log", activity, auth=True)
            if success:
                print(f"  {GREEN}✓{RESET} Activity {i}: {activity['event']} for {activity['duration_seconds']}s in {activity.get('application', 'N/A')}")
                self.created_items["activities"].append(response)
            else:
                print(f"  {RED}✗{RESET} Activity {i} failed: {error}")
            time.sleep(0.2)  # Small delay
        
        # Get today's activities
        print(f"\n{CYAN}Retrieving today's activities...{RESET}")
        success, response, error = self.make_request("GET", f"/api/v1/monitoring/activity/{self.user_id}/today", auth=True)
        if success:
            activities = response if isinstance(response, list) else []
            total_time = sum(a.get('duration_seconds', 0) for a in activities)
            print(f"  {GREEN}✓{RESET} Found {len(activities)} activities")
            print(f"  {GREEN}✓{RESET} Total active time: {total_time/60:.1f} minutes")
        else:
            print(f"  {RED}✗{RESET} Failed to get activities: {error}")
        
        # Get productivity stats
        print(f"\n{CYAN}Getting productivity statistics...{RESET}")
        success, response, error = self.make_request("GET", f"/api/v1/monitoring/stats/{self.user_id}/productivity", auth=True)
        if success:
            print(f"  {GREEN}✓{RESET} Productivity stats retrieved")
            if isinstance(response, dict):
                print(f"  {CYAN}→{RESET} Stats: {json.dumps(response, indent=2)}")
        else:
            print(f"  {RED}✗{RESET} Failed to get stats: {error}")
        
        # Get team activity
        if self.org_id:
            print(f"\n{CYAN}Getting team activity...{RESET}")
            success, response, error = self.make_request("GET", f"/api/v1/monitoring/team/{self.org_id}", auth=True)
            if success:
                team_activities = response if isinstance(response, list) else []
                print(f"  {GREEN}✓{RESET} Team has {len(team_activities)} total activities")
            else:
                print(f"  {RED}✗{RESET} Failed to get team activity: {error}")
    
    def test_performance_management(self):
        """Test performance management features"""
        print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
        print(f"{BOLD}{BLUE}🎯 Test 2: Performance Management (EPR){RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")
        
        # Create multiple goals
        goals = [
            {
                "title": "Master Python Testing",
                "description": "Learn pytest, unittest, and integration testing",
                "goal_type": "skill_based",
                "target_value": 100,
                "start_date": datetime.now().isoformat(),
                "target_date": (datetime.now() + timedelta(days=30)).isoformat()
            },
            {
                "title": "Complete Microservices Integration",
                "description": "Successfully integrate all 4 microservices",
                "goal_type": "qualitative",
                "start_date": datetime.now().isoformat(),
                "target_date": (datetime.now() + timedelta(days=7)).isoformat()
            },
            {
                "title": "Increase Code Coverage",
                "description": "Achieve 80% code coverage on all projects",
                "goal_type": "quantitative",
                "target_value": 80,
                "current_value": 45,
                "start_date": datetime.now().isoformat(),
                "target_date": (datetime.now() + timedelta(days=14)).isoformat()
            }
        ]
        
        print(f"{CYAN}Creating 3 performance goals...{RESET}")
        for i, goal in enumerate(goals, 1):
            success, response, error = self.make_request("POST", "/api/v1/performance/goals", goal, auth=True)
            if success:
                print(f"  {GREEN}✓{RESET} Goal {i}: {goal['title']}")
                self.created_items["goals"].append(response)
            else:
                print(f"  {RED}✗{RESET} Goal {i} failed: {error}")
            time.sleep(0.1)
        
        # Retrieve all goals
        print(f"\n{CYAN}Retrieving all goals...{RESET}")
        success, response, error = self.make_request("GET", f"/api/v1/performance/user/{self.user_id}/goals", auth=True)
        if success:
            goals_list = response if isinstance(response, list) else []
            print(f"  {GREEN}✓{RESET} Found {len(goals_list)} goals")
            for goal in goals_list:
                status = goal.get('status', 'unknown')
                print(f"    • {goal.get('title', 'Untitled')} - Status: {status}")
        else:
            print(f"  {RED}✗{RESET} Failed to get goals: {error}")
        
        # Get skills
        print(f"\n{CYAN}Getting skills assessment...{RESET}")
        success, response, error = self.make_request("GET", f"/api/v1/performance/user/{self.user_id}/skills", auth=True)
        if success:
            skills = response if isinstance(response, list) else []
            print(f"  {GREEN}✓{RESET} Found {len(skills)} skills")
        else:
            print(f"  {RED}✗{RESET} Failed to get skills: {error}")
        
        # Get reviews
        print(f"\n{CYAN}Getting performance reviews...{RESET}")
        success, response, error = self.make_request("GET", f"/api/v1/performance/user/{self.user_id}/reviews", auth=True)
        if success:
            reviews = response if isinstance(response, list) else []
            print(f"  {GREEN}✓{RESET} Found {len(reviews)} reviews")
        else:
            print(f"  {RED}✗{RESET} Failed to get reviews: {error}")
        
        # Get team performance
        if self.org_id:
            print(f"\n{CYAN}Getting team performance metrics...{RESET}")
            success, response, error = self.make_request("GET", f"/api/v1/performance/team/{self.org_id}/performance", auth=True)
            if success:
                print(f"  {GREEN}✓{RESET} Team performance data retrieved")
            else:
                print(f"  {RED}✗{RESET} Failed to get team performance: {error}")
    
    def test_research_collaboration(self):
        """Test research lab features"""
        print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
        print(f"{BOLD}{BLUE}🔬 Test 3: Research Labs & Collaboration{RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")
        
        # Create labs
        labs = [
            {
                "name": "AI Research Lab",
                "description": "Machine learning and deep learning research",
                "field": "Artificial Intelligence"
            },
            {
                "name": "Data Science Lab",
                "description": "Data analysis and visualization",
                "field": "Data Science"
            },
            {
                "name": "Quantum Computing Lab",
                "description": "Quantum algorithms research",
                "field": "Quantum Physics"
            }
        ]
        
        print(f"{CYAN}Creating 3 research labs...{RESET}")
        for i, lab in enumerate(labs, 1):
            success, response, error = self.make_request("POST", "/api/v1/research/labs", lab, auth=True)
            if success:
                print(f"  {GREEN}✓{RESET} Lab {i}: {lab['name']}")
                self.created_items["labs"].append(response)
            else:
                print(f"  {RED}✗{RESET} Lab {i} failed: {error}")
            time.sleep(0.1)
        
        # Get all labs
        print(f"\n{CYAN}Retrieving all labs...{RESET}")
        success, response, error = self.make_request("GET", "/api/v1/research/labs", auth=True)
        if success:
            labs_list = response if isinstance(response, list) else []
            print(f"  {GREEN}✓{RESET} Found {len(labs_list)} labs")
            for lab in labs_list:
                print(f"    • {lab.get('name', 'Untitled')} - Field: {lab.get('field', 'N/A')}")
        else:
            print(f"  {RED}✗{RESET} Failed to get labs: {error}")
        
        # Add researchers
        print(f"\n{CYAN}Adding researchers...{RESET}")
        researcher_data = {
            "name": "Dr. John Researcher",
            "email": "john.researcher@example.com",
            "position": "Senior Researcher",
            "expertise": "Machine Learning, NLP"
        }
        success, response, error = self.make_request("POST", "/api/v1/research/researchers", researcher_data, auth=True)
        if success:
            print(f"  {GREEN}✓{RESET} Researcher added: {researcher_data['name']}")
        else:
            print(f"  {RED}✗{RESET} Failed to add researcher: {error}")
        
        # Get researchers
        print(f"\n{CYAN}Getting all researchers...{RESET}")
        success, response, error = self.make_request("GET", "/api/v1/research/researchers", auth=True)
        if success:
            researchers = response if isinstance(response, list) else []
            print(f"  {GREEN}✓{RESET} Found {len(researchers)} researchers")
        else:
            print(f"  {RED}✗{RESET} Failed to get researchers: {error}")
        
        # Get collaborations
        print(f"\n{CYAN}Getting collaborations...{RESET}")
        success, response, error = self.make_request("GET", "/api/v1/research/collaborations", auth=True)
        if success:
            collabs = response if isinstance(response, list) else []
            print(f"  {GREEN}✓{RESET} Found {len(collabs)} collaborations")
        else:
            print(f"  {RED}✗{RESET} Failed to get collaborations: {error}")
    
    def test_projects_integration(self):
        """Test project management (Atlas)"""
        print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
        print(f"{BOLD}{BLUE}📋 Test 4: Project Management (Atlas){RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")
        
        # Get projects
        print(f"{CYAN}Getting all projects...{RESET}")
        success, response, error = self.make_request("GET", "/api/v1/projects/", auth=True)
        if success:
            projects = response if isinstance(response, list) else []
            print(f"  {GREEN}✓{RESET} Found {len(projects)} projects")
            
            if projects:
                for project in projects[:3]:  # Show first 3
                    print(f"    • {project.get('name', 'Untitled')} - Status: {project.get('status', 'N/A')}")
                    self.created_items["projects"].append(project)
        else:
            print(f"  {RED}✗{RESET} Failed to get projects: {error}")
    
    def test_unified_dashboard(self):
        """Test the unified dashboard aggregation"""
        print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
        print(f"{BOLD}{BLUE}📊 Test 5: Unified Dashboard Aggregation{RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")
        
        print(f"{CYAN}Loading unified dashboard...{RESET}")
        success, response, error = self.make_request("GET", "/api/v1/dashboard", auth=True)
        
        if success:
            print(f"  {GREEN}✓{RESET} Dashboard loaded successfully\n")
            
            # Show dashboard sections
            sections = []
            if response.get("projects"):
                sections.append("projects")
                projects = response["projects"]
                if isinstance(projects, dict):
                    count = projects.get("total", 0)
                else:
                    count = len(projects) if isinstance(projects, list) else 0
                print(f"  {CYAN}📋 Projects:{RESET} {count} total")
            
            if response.get("activity"):
                sections.append("activity")
                activity = response["activity"]
                if isinstance(activity, dict):
                    print(f"  {CYAN}📊 Activity:{RESET} {activity.get('today_count', 0)} activities today")
                elif isinstance(activity, list):
                    print(f"  {CYAN}📊 Activity:{RESET} {len(activity)} activities")
            
            if response.get("performance"):
                sections.append("performance")
                perf = response["performance"]
                if isinstance(perf, dict):
                    goals = perf.get("goals", [])
                    print(f"  {CYAN}🎯 Performance:{RESET} {len(goals)} active goals")
            
            if response.get("research"):
                sections.append("research")
                research = response["research"]
                if isinstance(research, dict):
                    labs = research.get("labs", [])
                    print(f"  {CYAN}🔬 Research:{RESET} {len(labs)} labs")
            
            print(f"\n  {GREEN}✓{RESET} Dashboard contains: {', '.join(sections)}")
        else:
            print(f"  {RED}✗{RESET} Failed to load dashboard: {error}")
    
    def show_summary(self):
        """Show test summary"""
        print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
        print(f"{BOLD}{CYAN}📊 Test Summary{RESET}")
        print(f"{CYAN}{'='*60}{RESET}\n")
        
        print(f"{GREEN}Created Items:{RESET}")
        print(f"  • Activities: {len(self.created_items['activities'])}")
        print(f"  • Goals: {len(self.created_items['goals'])}")
        print(f"  • Labs: {len(self.created_items['labs'])}")
        print(f"  • Projects: {len(self.created_items['projects'])}")
        
        print(f"\n{GREEN}Test User:{RESET}")
        print(f"  • Email: {self.test_email}")
        print(f"  • User ID: {self.user_id}")
        print(f"  • Organization ID: {self.org_id}")
        
        if self.token:
            print(f"\n{GREEN}Authentication Token:{RESET}")
            print(f"  {self.token[:80]}...")
        
        print(f"\n{BOLD}{GREEN}✓ All monitoring tests completed!{RESET}\n")
    
    def run_all_tests(self):
        """Run all monitoring tests"""
        print(f"\n{BOLD}{'='*60}{RESET}")
        print(f"{BOLD}🧪 Enhanced Monitoring Test Suite{RESET}")
        print(f"{BOLD}{'='*60}{RESET}")
        print(f"Base URL: {self.base_url}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        if not self.setup():
            print(f"\n{RED}Setup failed! Cannot continue tests.{RESET}\n")
            return False
        
        # Run all test suites
        self.test_activity_monitoring()
        self.test_performance_management()
        self.test_research_collaboration()
        self.test_projects_integration()
        self.test_unified_dashboard()
        
        # Show summary
        self.show_summary()
        
        return True


def main():
    """Main entry point"""
    suite = MonitoringTestSuite()
    success = suite.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
