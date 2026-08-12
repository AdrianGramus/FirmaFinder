import requests
import sys
import json
from datetime import datetime

class CRMAPITester:
    def __init__(self, base_url="https://firmafinder-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_token = "test_session_001"
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.session_token}'
        }
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "status": "PASSED" if success else "FAILED",
            "details": details
        })

    def test_search_soft_bucuresti(self):
        """Test search SOFT companies in BUCURESTI (county 40)"""
        try:
            response = requests.get(f"{self.api_url}/search", 
                                  params={"q": "SOFT", "county": "40"})
            success = response.status_code == 200
            if success:
                data = response.json()
                success = "companies" in data and len(data.get("companies", [])) > 0
                details = f"Found {len(data.get('companies', []))} companies for SOFT in BUCURESTI"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            self.log_test("Search SOFT in BUCURESTI (county 40)", success, details)
            return success
        except Exception as e:
            self.log_test("Search SOFT in BUCURESTI (county 40)", False, str(e))
            return False

    def test_search_auto_timis(self):
        """Test search AUTO companies in TIMIS (county 35)"""
        try:
            response = requests.get(f"{self.api_url}/search", 
                                  params={"q": "AUTO", "county": "35"})
            success = response.status_code == 200
            if success:
                data = response.json()
                success = "companies" in data
                details = f"Found {len(data.get('companies', []))} companies for AUTO in TIMIS"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            self.log_test("Search AUTO in TIMIS (county 35)", success, details)
            return success
        except Exception as e:
            self.log_test("Search AUTO in TIMIS (county 35)", False, str(e))
            return False

    def test_counties_endpoint(self):
        """Test counties endpoint returns 42 counties"""
        try:
            response = requests.get(f"{self.api_url}/counties")
            success = response.status_code == 200
            if success:
                data = response.json()
                success = isinstance(data, list) and len(data) == 42
                details = f"Retrieved {len(data)} counties (expected 42)"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            self.log_test("Get counties (should return 42)", success, details)
            return success
        except Exception as e:
            self.log_test("Get counties (should return 42)", False, str(e))
            return False

    def test_caen_codes_flat(self):
        """Test CAEN codes flat list"""
        try:
            response = requests.get(f"{self.api_url}/caen-codes/flat")
            success = response.status_code == 200
            if success:
                data = response.json()
                success = isinstance(data, list) and len(data) > 0
                details = f"Retrieved {len(data)} CAEN codes"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            self.log_test("Get CAEN codes flat list", success, details)
            return success
        except Exception as e:
            self.log_test("Get CAEN codes flat list", False, str(e))
            return False

    def test_auth_me(self):
        """Test authentication endpoint"""
        try:
            response = requests.get(f"{self.api_url}/auth/me", headers=self.headers)
            success = response.status_code == 200
            if success:
                data = response.json()
                success = "user_id" in data
                details = f"Authenticated as user: {data.get('user_id', 'unknown')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            self.log_test("Authentication check", success, details)
            return success, response.json() if success else None
        except Exception as e:
            self.log_test("Authentication check", False, str(e))
            return False, None

    def test_create_company(self):
        """Test creating a company"""
        try:
            company_data = {
                "company_name": f"Test Company {datetime.now().strftime('%H%M%S')}",
                "cui": f"TEST{datetime.now().strftime('%H%M%S')}",
                "caen_code": "620",
                "caen_description": "Activitati de servicii in tehnologia informatiei",
                "email": "test@example.com",
                "phone": "+40123456789",
                "contact_person": "Test Contact",
                "address": "Test Address",
                "county": "BUCURESTI",
                "status": "potential_lead"
            }
            
            response = requests.post(f"{self.api_url}/companies", 
                                   json=company_data, headers=self.headers)
            success = response.status_code == 200
            if success:
                data = response.json()
                success = "id" in data and data.get("company_name") == company_data["company_name"]
                details = f"Created company with ID: {data.get('id')}"
                return success, data.get('id') if success else None
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                self.log_test("Create company", success, details)
                return False, None
            
        except Exception as e:
            self.log_test("Create company", False, str(e))
            return False, None

    def test_get_companies(self):
        """Test getting user companies"""
        try:
            response = requests.get(f"{self.api_url}/companies", headers=self.headers)
            success = response.status_code == 200
            if success:
                data = response.json()
                success = isinstance(data, list)
                details = f"Retrieved {len(data)} companies"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            self.log_test("Get user companies", success, details)
            return success
        except Exception as e:
            self.log_test("Get user companies", False, str(e))
            return False

    def test_update_company(self, company_id):
        """Test updating a company"""
        if not company_id:
            self.log_test("Update company", False, "No company ID provided")
            return False
            
        try:
            update_data = {"status": "prospect", "notes": "Updated by test"}
            response = requests.put(f"{self.api_url}/companies/{company_id}", 
                                  json=update_data, headers=self.headers)
            success = response.status_code == 200
            if success:
                data = response.json()
                success = data.get("status") == "prospect"
                details = f"Updated company status to: {data.get('status')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            self.log_test("Update company", success, details)
            return success
        except Exception as e:
            self.log_test("Update company", False, str(e))
            return False

    def test_create_reminder(self, company_id, company_name):
        """Test creating a reminder"""
        if not company_id:
            self.log_test("Create reminder", False, "No company ID provided")
            return False, None
            
        try:
            reminder_data = {
                "company_id": company_id,
                "company_name": company_name,
                "reminder_type": "call",
                "due_date": "2024-12-31T10:00:00Z",
                "message": "Test reminder"
            }
            
            response = requests.post(f"{self.api_url}/reminders", 
                                   json=reminder_data, headers=self.headers)
            success = response.status_code == 200
            if success:
                data = response.json()
                success = "id" in data
                details = f"Created reminder with ID: {data.get('id')}"
                return success, data.get('id')
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                self.log_test("Create reminder", success, details)
                return False, None
        except Exception as e:
            self.log_test("Create reminder", False, str(e))
            return False, None

    def test_get_reminders(self):
        """Test getting reminders"""
        try:
            response = requests.get(f"{self.api_url}/reminders", headers=self.headers)
            success = response.status_code == 200
            if success:
                data = response.json()
                success = isinstance(data, list)
                details = f"Retrieved {len(data)} reminders"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            self.log_test("Get reminders", success, details)
            return success
        except Exception as e:
            self.log_test("Get reminders", False, str(e))
            return False

    def test_complete_reminder(self, reminder_id):
        """Test completing a reminder"""
        if not reminder_id:
            self.log_test("Complete reminder", False, "No reminder ID provided")
            return False
            
        try:
            response = requests.post(f"{self.api_url}/reminders/{reminder_id}/complete", 
                                   headers=self.headers)
            success = response.status_code == 200
            if success:
                data = response.json()
                success = data.get("is_completed") == True
                details = f"Reminder marked as completed"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            self.log_test("Complete reminder", success, details)
            return success
        except Exception as e:
            self.log_test("Complete reminder", False, str(e))
            return False

    def test_get_notifications(self):
        """Test getting notifications"""
        try:
            response = requests.get(f"{self.api_url}/notifications", headers=self.headers)
            success = response.status_code == 200
            if success:
                data = response.json()
                success = isinstance(data, list)
                details = f"Retrieved {len(data)} notifications"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            self.log_test("Get notifications", success, details)
            return success
        except Exception as e:
            self.log_test("Get notifications", False, str(e))
            return False

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        try:
            response = requests.get(f"{self.api_url}/dashboard/stats", headers=self.headers)
            success = response.status_code == 200
            if success:
                data = response.json()
                required_fields = ["total_companies", "potential_leads", "prospects", "clients"]
                success = all(field in data for field in required_fields)
                details = f"Stats: {data.get('total_companies', 0)} total companies"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            self.log_test("Get dashboard stats", success, details)
            return success
        except Exception as e:
            self.log_test("Get dashboard stats", False, str(e))
            return False

    def test_ai_compose_message(self):
        """Test AI message composition"""
        try:
            ai_data = {
                "company_name": "Test Company",
                "contact_person": "John Doe",
                "email": "john@test.com",
                "context": "Initial business outreach",
                "language": "en"
            }
            
            response = requests.post(f"{self.api_url}/ai/compose-message", 
                                   json=ai_data, headers=self.headers)
            success = response.status_code == 200
            if success:
                data = response.json()
                success = "message" in data and len(data.get("message", "")) > 0
                details = f"Generated message length: {len(data.get('message', ''))}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            self.log_test("AI compose message", success, details)
            return success
        except Exception as e:
            self.log_test("AI compose message", False, str(e))
            return False

    def test_delete_company(self, company_id):
        """Test deleting a company"""
        if not company_id:
            self.log_test("Delete company", False, "No company ID provided")
            return False
            
        try:
            response = requests.delete(f"{self.api_url}/companies/{company_id}", 
                                     headers=self.headers)
            success = response.status_code == 200
            if success:
                data = response.json()
                success = data.get("status") == "deleted"
                details = "Company successfully deleted"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            self.log_test("Delete company", success, details)
            return success
        except Exception as e:
            self.log_test("Delete company", False, str(e))
            return False

    def run_all_tests(self):
        """Run all API tests"""
        print(f"🔍 Starting CRM API Tests against {self.base_url}")
        print("=" * 60)
        
        # Test public endpoints first
        self.test_search_soft_bucuresti()
        self.test_search_auto_timis()
        self.test_counties_endpoint()
        self.test_caen_codes_flat()
        
        # Test authentication
        auth_success, user_data = self.test_auth_me()
        if not auth_success:
            print("❌ Authentication failed - skipping authenticated tests")
            return self.get_summary()
        
        # Test authenticated endpoints
        self.test_get_companies()
        self.test_get_reminders()
        self.test_get_notifications()
        self.test_dashboard_stats()
        
        # Test CRUD operations
        company_success, company_id = self.test_create_company()
        if company_success and company_id:
            self.test_update_company(company_id)
            
            # Create and test reminder
            reminder_success, reminder_id = self.test_create_reminder(
                company_id, f"Test Company {datetime.now().strftime('%H%M%S')}"
            )
            if reminder_success and reminder_id:
                self.test_complete_reminder(reminder_id)
            
            # Clean up - delete test company
            self.test_delete_company(company_id)
        
        # Test AI functionality
        self.test_ai_compose_message()
        
        return self.get_summary()

    def get_summary(self):
        """Get test summary"""
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    """Main test runner"""
    tester = CRMAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    with open('/app/test_reports/backend_api_results.json', 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_tests": tester.tests_run,
            "passed_tests": tester.tests_passed,
            "success_rate": f"{(tester.tests_passed/tester.tests_run*100):.1f}%" if tester.tests_run > 0 else "0%",
            "results": tester.test_results
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())