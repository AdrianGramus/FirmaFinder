"""
FirmaFinder CRM API Tests
Tests for: Auth, CAEN codes, Counties, Search, Companies CRUD, Reminders CRUD, Dashboard
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://firmafinder-1.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@firmafinder.com"
ADMIN_PASSWORD = "Admin123!"


class TestPublicEndpoints:
    """Test endpoints that don't require authentication"""
    
    def test_caen_codes_returns_exactly_9_codes(self):
        """GET /api/caen-codes - should return exactly 9 printing CAEN codes"""
        response = requests.get(f"{BASE_URL}/api/caen-codes")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) == 9, f"Expected exactly 9 CAEN codes, got {len(data)}"
        
        # Verify expected CAEN codes are present
        expected_codes = ["1811", "1812", "1813", "1814", "1721", "1330", "2222", "7311", "8219"]
        actual_codes = [c["code"] for c in data]
        for code in expected_codes:
            assert code in actual_codes, f"Missing CAEN code: {code}"
        
        # Verify structure
        for item in data:
            assert "code" in item, "Each item should have 'code'"
            assert "description_ro" in item, "Each item should have 'description_ro'"
            assert "description_en" in item, "Each item should have 'description_en'"
        print(f"✓ CAEN codes endpoint returns exactly 9 codes: {actual_codes}")
    
    def test_counties_returns_romanian_counties(self):
        """GET /api/counties - should return Romanian counties"""
        response = requests.get(f"{BASE_URL}/api/counties")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) >= 40, f"Expected at least 40 counties, got {len(data)}"
        
        # Verify structure
        for item in data:
            assert "code" in item, "Each county should have 'code'"
            assert "name" in item, "Each county should have 'name'"
        
        # Check for Bucuresti (code 40)
        bucuresti = next((c for c in data if c["code"] == "40"), None)
        assert bucuresti is not None, "Bucuresti (code 40) should be present"
        assert bucuresti["name"] == "BUCURESTI", f"Expected BUCURESTI, got {bucuresti['name']}"
        print(f"✓ Counties endpoint returns {len(data)} Romanian counties")


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_login_with_valid_credentials(self):
        """POST /api/auth/login - login with email + password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert "user_id" in data, "Response should contain user_id"
        assert data["email"] == ADMIN_EMAIL, f"Expected email {ADMIN_EMAIL}, got {data['email']}"
        assert len(data["token"]) > 0, "Token should not be empty"
        print(f"✓ Login successful for {ADMIN_EMAIL}")
    
    def test_login_with_invalid_credentials(self):
        """POST /api/auth/login - should fail with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": ADMIN_EMAIL,
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Login correctly rejects invalid credentials")
    
    def test_register_new_user(self):
        """POST /api/auth/register - register with email + phone + password"""
        unique_email = f"test_{uuid.uuid4().hex[:8]}@test.com"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "phone": "+40712345678",
            "password": "TestPass123!",
            "name": "Test User"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert data["email"] == unique_email.lower(), f"Expected email {unique_email.lower()}"
        assert data["phone"] == "+40712345678", "Phone should be saved"
        print(f"✓ Registration successful for {unique_email}")
    
    def test_register_requires_email(self):
        """POST /api/auth/register - email is required"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": "",
            "password": "TestPass123!"
        })
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Registration correctly requires email")
    
    def test_auth_me_with_valid_token(self):
        """GET /api/auth/me - returns current user info"""
        # First login to get token
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = login_resp.json()["token"]
        
        # Then check /auth/me
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["email"] == ADMIN_EMAIL, f"Expected {ADMIN_EMAIL}, got {data['email']}"
        assert "password_hash" not in data, "Password hash should not be exposed"
        print(f"✓ /auth/me returns user info for {ADMIN_EMAIL}")
    
    def test_auth_me_without_token(self):
        """GET /api/auth/me - should fail without token"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ /auth/me correctly requires authentication")


class TestSearch:
    """Test search endpoints - uses live mfinante.gov.ro data"""
    
    def test_search_by_caen_code(self):
        """GET /api/search/caen/{code} - search by CAEN code"""
        # Use CAEN 1812 (printing activities) with Bucuresti county
        response = requests.get(f"{BASE_URL}/api/search/caen/1812", params={"county": "40"}, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "companies" in data, "Response should contain 'companies'"
        assert "total" in data, "Response should contain 'total'"
        assert data["caen_code"] == "1812", f"Expected caen_code 1812, got {data.get('caen_code')}"
        assert data["source"] == "mfinante.gov.ro", "Source should be mfinante.gov.ro"
        
        # Should return some companies (live data)
        print(f"✓ CAEN search for 1812 returned {data['total']} companies from mfinante.gov.ro")
    
    def test_search_by_name(self):
        """GET /api/search?q=TIPAR - search companies by name"""
        response = requests.get(f"{BASE_URL}/api/search", params={
            "q": "TIPAR",
            "county": "40"
        }, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "companies" in data, "Response should contain 'companies'"
        assert "total" in data, "Response should contain 'total'"
        assert data["query"] == "TIPAR", f"Expected query TIPAR, got {data.get('query')}"
        print(f"✓ Name search for 'TIPAR' returned {data['total']} companies")
    
    def test_search_requires_query(self):
        """GET /api/search - should fail without query"""
        response = requests.get(f"{BASE_URL}/api/search", params={"county": "40"})
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Search correctly requires query parameter")


class TestCompanyCRUD:
    """Test company CRUD operations - requires authentication"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_resp.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_create_company(self):
        """POST /api/companies - save a company"""
        company_data = {
            "company_name": f"TEST_Company_{uuid.uuid4().hex[:8]}",
            "cui": f"TEST{uuid.uuid4().hex[:6]}",
            "caen_code": "1812",
            "caen_description": "Alte activitati de tiparire",
            "county": "BUCURESTI",
            "status": "potential_lead"
        }
        response = requests.post(f"{BASE_URL}/api/companies", json=company_data, headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain 'id'"
        assert data["company_name"] == company_data["company_name"]
        assert data["status"] == "potential_lead"
        
        # Verify with GET
        get_resp = requests.get(f"{BASE_URL}/api/companies/{data['id']}", headers=self.headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["company_name"] == company_data["company_name"]
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/companies/{data['id']}", headers=self.headers)
        print(f"✓ Company created and verified: {company_data['company_name']}")
    
    def test_list_companies(self):
        """GET /api/companies - list saved companies"""
        response = requests.get(f"{BASE_URL}/api/companies", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Listed {len(data)} companies")
    
    def test_update_company_status(self):
        """PUT /api/companies/{id} - update company status"""
        # Create a company first
        create_resp = requests.post(f"{BASE_URL}/api/companies", json={
            "company_name": f"TEST_Update_{uuid.uuid4().hex[:8]}",
            "cui": f"TEST{uuid.uuid4().hex[:6]}",
            "status": "potential_lead"
        }, headers=self.headers)
        company_id = create_resp.json()["id"]
        
        # Update status
        update_resp = requests.put(f"{BASE_URL}/api/companies/{company_id}", json={
            "status": "prospect"
        }, headers=self.headers)
        assert update_resp.status_code == 200, f"Expected 200, got {update_resp.status_code}"
        assert update_resp.json()["status"] == "prospect"
        
        # Verify with GET
        get_resp = requests.get(f"{BASE_URL}/api/companies/{company_id}", headers=self.headers)
        assert get_resp.json()["status"] == "prospect"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/companies/{company_id}", headers=self.headers)
        print("✓ Company status updated from potential_lead to prospect")
    
    def test_delete_company(self):
        """DELETE /api/companies/{id} - delete company"""
        # Create a company first
        create_resp = requests.post(f"{BASE_URL}/api/companies", json={
            "company_name": f"TEST_Delete_{uuid.uuid4().hex[:8]}",
            "cui": f"TEST{uuid.uuid4().hex[:6]}"
        }, headers=self.headers)
        company_id = create_resp.json()["id"]
        
        # Delete
        delete_resp = requests.delete(f"{BASE_URL}/api/companies/{company_id}", headers=self.headers)
        assert delete_resp.status_code == 200, f"Expected 200, got {delete_resp.status_code}"
        
        # Verify deleted
        get_resp = requests.get(f"{BASE_URL}/api/companies/{company_id}", headers=self.headers)
        assert get_resp.status_code == 404, "Company should be deleted"
        print("✓ Company deleted successfully")
    
    def test_company_requires_auth(self):
        """POST /api/companies - should fail without auth"""
        response = requests.post(f"{BASE_URL}/api/companies", json={
            "company_name": "Test Company"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Company creation correctly requires authentication")


class TestReminderCRUD:
    """Test reminder CRUD operations - requires authentication"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token and create a test company"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_resp.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create a test company for reminders
        company_resp = requests.post(f"{BASE_URL}/api/companies", json={
            "company_name": f"TEST_ReminderCompany_{uuid.uuid4().hex[:8]}",
            "cui": f"TEST{uuid.uuid4().hex[:6]}"
        }, headers=self.headers)
        self.test_company = company_resp.json()
    
    def teardown_method(self, method):
        """Cleanup test company"""
        if hasattr(self, 'test_company') and self.test_company:
            requests.delete(f"{BASE_URL}/api/companies/{self.test_company['id']}", headers=self.headers)
    
    def test_create_reminder(self):
        """POST /api/reminders - create reminder for a company"""
        reminder_data = {
            "company_id": self.test_company["id"],
            "company_name": self.test_company["company_name"],
            "reminder_type": "call",
            "due_date": "2026-02-15T10:00:00Z",
            "message": "Follow up call"
        }
        response = requests.post(f"{BASE_URL}/api/reminders", json=reminder_data, headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain 'id'"
        assert data["company_id"] == self.test_company["id"]
        assert data["reminder_type"] == "call"
        assert data["is_completed"] == False
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/reminders/{data['id']}", headers=self.headers)
        print(f"✓ Reminder created for {self.test_company['company_name']}")
    
    def test_list_reminders(self):
        """GET /api/reminders - list reminders"""
        response = requests.get(f"{BASE_URL}/api/reminders", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Listed {len(data)} reminders")
    
    def test_complete_reminder(self):
        """POST /api/reminders/{id}/complete - mark reminder complete"""
        # Create reminder
        create_resp = requests.post(f"{BASE_URL}/api/reminders", json={
            "company_id": self.test_company["id"],
            "company_name": self.test_company["company_name"],
            "reminder_type": "email",
            "due_date": "2026-02-15T10:00:00Z"
        }, headers=self.headers)
        reminder_id = create_resp.json()["id"]
        
        # Complete it
        complete_resp = requests.post(f"{BASE_URL}/api/reminders/{reminder_id}/complete", headers=self.headers)
        assert complete_resp.status_code == 200, f"Expected 200, got {complete_resp.status_code}"
        assert complete_resp.json()["is_completed"] == True
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/reminders/{reminder_id}", headers=self.headers)
        print("✓ Reminder marked as complete")
    
    def test_delete_reminder(self):
        """DELETE /api/reminders/{id} - delete reminder"""
        # Create reminder
        create_resp = requests.post(f"{BASE_URL}/api/reminders", json={
            "company_id": self.test_company["id"],
            "company_name": self.test_company["company_name"],
            "reminder_type": "message",
            "due_date": "2026-02-15T10:00:00Z"
        }, headers=self.headers)
        reminder_id = create_resp.json()["id"]
        
        # Delete
        delete_resp = requests.delete(f"{BASE_URL}/api/reminders/{reminder_id}", headers=self.headers)
        assert delete_resp.status_code == 200, f"Expected 200, got {delete_resp.status_code}"
        print("✓ Reminder deleted successfully")


class TestDashboard:
    """Test dashboard stats endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_resp.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_dashboard_stats(self):
        """GET /api/dashboard/stats - returns pipeline stats"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Verify all expected fields
        expected_fields = [
            "total_companies", "potential_leads", "prospects", "clients", "rejected",
            "upcoming_reminders", "overdue_reminders", "unread_notifications", "recent_companies"
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        # Verify types
        assert isinstance(data["total_companies"], int)
        assert isinstance(data["upcoming_reminders"], list)
        assert isinstance(data["recent_companies"], list)
        print(f"✓ Dashboard stats: {data['total_companies']} companies, {data['potential_leads']} leads, {data['prospects']} prospects, {data['clients']} clients")
    
    def test_dashboard_requires_auth(self):
        """GET /api/dashboard/stats - should fail without auth"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Dashboard correctly requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
