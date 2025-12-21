"""
Simple endpoint test - tests endpoints that actually exist
"""
import asyncio
import aiohttp
import json
from datetime import datetime

BASE_URL = "http://localhost:9000/api/v1"

class SimpleEndpointTester:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.org_id = None
        
    async def setup_auth(self):
        """Setup: Register and login a test user"""
        print("\n" + "="*70)
        print("SETUP: Creating test user")
        print("="*70)
        
        payload = {
            "email": f"testuser_{datetime.now().timestamp()}@example.com",
            "name": "Test User",
            "password": "TestPassword123!",
            "role": "admin"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BASE_URL}/auth/register", json=payload) as resp:
                data = await resp.json()
                if resp.status == 200:
                    self.token = data.get("access_token")
                    self.user_id = data.get("user", {}).get("id")
                    self.org_id = data.get("user", {}).get("organization_id")
                    print(f"✓ User created: {payload['email']}")
                    return True
                else:
                    print(f"✗ Setup failed: {data}")
                    return False
    
    def get_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.token}"}
    
    async def test_endpoint(self, method: str, path: str, name: str, data: dict = None):
        """Test a single endpoint"""
        url = f"{BASE_URL}{path}"
        async with aiohttp.ClientSession() as session:
            try:
                if method == "GET":
                    async with session.get(url, headers=self.get_headers()) as resp:
                        status = resp.status
                elif method == "POST":
                    async with session.post(url, json=data, headers=self.get_headers()) as resp:
                        status = resp.status
                else:
                    status = 0
                
                symbol = "✓" if status < 400 else "✗"
                print(f"{symbol} {method:6} {path:50} {status}")
                return status < 400
            except Exception as e:
                print(f"✗ {method:6} {path:50} ERROR: {str(e)[:30]}")
                return False
    
    async def run_all_tests(self):
        """Run all endpoint tests"""
        print("\n" + "="*70)
        print("SIMPLE ENDPOINT TEST SUITE")
        print("="*70)
        print(f"Base URL: {BASE_URL}")
        
        # Setup
        if not await self.setup_auth():
            print("\n✗ Setup failed - cannot continue")
            return
        
        print("\n" + "="*70)
        print("TESTING ENDPOINTS")
        print("="*70)
        
        results = {}
        
        # Health
        print("\n[HEALTH]")
        results["health"] = await self.test_endpoint("GET", "/health", "Health Check")
        
        # Auth
        print("\n[AUTH]")
        results["auth_me"] = await self.test_endpoint("GET", "/auth/me", "Get Current User")
        results["auth_orgs"] = await self.test_endpoint("GET", "/auth/organizations", "List Organizations")
        
        # Projects
        print("\n[PROJECTS]")
        results["projects_list"] = await self.test_endpoint("GET", "/projects", "List Projects")
        results["projects_create"] = await self.test_endpoint("POST", "/projects", "Create Project", {
            "name": f"Test Project {datetime.now().timestamp()}",
            "description": "Test"
        })
        
        # Activities
        print("\n[ACTIVITIES]")
        results["activities_list"] = await self.test_endpoint("GET", "/activities", "List Activities")
        
        # Performance
        print("\n[PERFORMANCE]")
        results["perf_reviews"] = await self.test_endpoint("GET", f"/performance/users/{self.user_id}/reviews", "Get Reviews")
        results["perf_goals"] = await self.test_endpoint("GET", f"/performance/users/{self.user_id}/goals", "Get Goals")
        results["perf_feedback"] = await self.test_endpoint("GET", f"/performance/users/{self.user_id}/feedback", "Get Feedback")
        
        # Monitoring
        print("\n[MONITORING]")
        results["monitoring_activity"] = await self.test_endpoint("GET", f"/monitoring/activity/{self.user_id}", "User Activity")
        results["monitoring_team"] = await self.test_endpoint("GET", f"/monitoring/team/{self.org_id}", "Team Activity")
        
        # Research
        print("\n[RESEARCH]")
        results["research_labs"] = await self.test_endpoint("GET", "/research/labs", "List Labs")
        results["research_researchers"] = await self.test_endpoint("GET", "/research/researchers", "List Researchers")
        
        # Dashboard
        print("\n[DASHBOARD]")
        results["dashboard"] = await self.test_endpoint("GET", "/dashboard", "Unified Dashboard")
        
        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{test_name:30} {status}")
        
        print("="*70)
        print(f"Total: {passed}/{total} tests passed ({int(passed/total*100)}%)")
        print("="*70)


async def main():
    tester = SimpleEndpointTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
