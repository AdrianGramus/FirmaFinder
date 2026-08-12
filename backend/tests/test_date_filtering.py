"""
Test suite for the NEW date filtering feature in FirmaFinder CRM.
Tests the since_date parameter for CAEN search and name search endpoints.
The establishment_date comes from ANAF API (data_inregistrare field).
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestDateFilteringFeature:
    """Tests for the new establishment date filtering feature"""
    
    def test_caen_search_without_date_filter(self):
        """CAEN 1812 search without date filter returns all companies (~243)"""
        response = requests.get(
            f"{BASE_URL}/api/search/caen/1812",
            params={"county": "40"},
            timeout=90
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should return many companies (around 243)
        assert data["total"] >= 200, f"Expected ~243 companies, got {data['total']}"
        assert data["since_date"] == ""
        assert len(data["companies"]) == data["total"]
        
        # Verify establishment_date is populated from ANAF
        companies_with_dates = [c for c in data["companies"] if c.get("establishment_date")]
        assert len(companies_with_dates) > 0, "No companies have establishment_date from ANAF"
        print(f"PASS: CAEN 1812 search returned {data['total']} companies, {len(companies_with_dates)} with establishment dates")
    
    def test_caen_search_with_since_date_2025(self):
        """CAEN 1812 search with since_date=2025-01-01 returns ~18 companies"""
        response = requests.get(
            f"{BASE_URL}/api/search/caen/1812",
            params={"county": "40", "since_date": "2025-01-01"},
            timeout=90
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should return fewer companies (around 18)
        assert data["total"] >= 10, f"Expected ~18 companies, got {data['total']}"
        assert data["total"] <= 30, f"Expected ~18 companies, got {data['total']}"
        assert data["since_date"] == "2025-01-01"
        
        # Verify ALL returned companies have establishment_date >= 2025-01-01
        for company in data["companies"]:
            est_date = company.get("establishment_date", "")
            assert est_date >= "2025-01-01", f"Company {company['cui']} has date {est_date} < 2025-01-01"
        
        print(f"PASS: CAEN 1812 with since_date=2025-01-01 returned {data['total']} companies, all >= 2025-01-01")
    
    def test_caen_search_with_since_date_2020(self):
        """CAEN 1812 search with since_date=2020-01-01 returns ~50 companies"""
        response = requests.get(
            f"{BASE_URL}/api/search/caen/1812",
            params={"county": "40", "since_date": "2020-01-01"},
            timeout=90
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should return more companies than 2025 filter but less than no filter
        assert data["total"] >= 40, f"Expected ~50 companies, got {data['total']}"
        assert data["total"] <= 70, f"Expected ~50 companies, got {data['total']}"
        assert data["since_date"] == "2020-01-01"
        
        # Verify ALL returned companies have establishment_date >= 2020-01-01
        for company in data["companies"]:
            est_date = company.get("establishment_date", "")
            assert est_date >= "2020-01-01", f"Company {company['cui']} has date {est_date} < 2020-01-01"
        
        print(f"PASS: CAEN 1812 with since_date=2020-01-01 returned {data['total']} companies, all >= 2020-01-01")
    
    def test_name_search_returns_establishment_dates(self):
        """Name search q=TIPAR returns companies with establishment_date from ANAF"""
        response = requests.get(
            f"{BASE_URL}/api/search",
            params={"q": "TIPAR", "county": "40"},
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] > 0, "Name search returned no results"
        
        # Verify establishment_date is populated
        companies_with_dates = [c for c in data["companies"] if c.get("establishment_date")]
        assert len(companies_with_dates) > 0, "No companies have establishment_date from ANAF"
        
        print(f"PASS: Name search q=TIPAR returned {data['total']} companies, {len(companies_with_dates)} with establishment dates")
    
    def test_name_search_with_date_filter(self):
        """Name search q=TIPAR with since_date=2020-01-01 filters correctly"""
        response = requests.get(
            f"{BASE_URL}/api/search",
            params={"q": "TIPAR", "county": "40", "since_date": "2020-01-01"},
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["since_date"] == "2020-01-01"
        
        # Verify ALL returned companies have establishment_date >= 2020-01-01
        for company in data["companies"]:
            est_date = company.get("establishment_date", "")
            assert est_date >= "2020-01-01", f"Company {company['cui']} has date {est_date} < 2020-01-01"
        
        print(f"PASS: Name search with since_date=2020-01-01 returned {data['total']} companies, all >= 2020-01-01")
    
    def test_anaf_data_includes_phone_and_j_number(self):
        """Verify ANAF enrichment includes phone and j_number when available"""
        response = requests.get(
            f"{BASE_URL}/api/search/caen/1812",
            params={"county": "40"},
            timeout=90
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check if any companies have phone numbers from ANAF
        companies_with_phone = [c for c in data["companies"] if c.get("phone")]
        companies_with_j_number = [c for c in data["companies"] if c.get("j_number")]
        
        # At least some companies should have phone/j_number from ANAF
        print(f"Companies with phone: {len(companies_with_phone)}/{data['total']}")
        print(f"Companies with j_number: {len(companies_with_j_number)}/{data['total']}")
        
        # Verify at least some have phone (ANAF provides this for many companies)
        assert len(companies_with_phone) > 0, "No companies have phone from ANAF"
        print(f"PASS: ANAF enrichment provides phone for {len(companies_with_phone)} companies")


class TestCaenCodesEndpoint:
    """Verify CAEN codes endpoint still works"""
    
    def test_caen_codes_returns_9_codes(self):
        """GET /api/caen-codes returns exactly 9 printing CAEN codes"""
        response = requests.get(f"{BASE_URL}/api/caen-codes", timeout=10)
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 9, f"Expected 9 CAEN codes, got {len(data)}"
        
        expected_codes = ["1811", "1812", "1813", "1814", "1721", "1330", "2222", "7311", "8219"]
        actual_codes = [c["code"] for c in data]
        
        for code in expected_codes:
            assert code in actual_codes, f"Missing CAEN code {code}"
        
        print(f"PASS: /api/caen-codes returns all 9 expected codes")


class TestAuthEndpoint:
    """Verify auth still works"""
    
    def test_login_works(self):
        """POST /api/auth/login with admin credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"identifier": "admin@firmafinder.com", "password": "Admin123!"},
            timeout=10
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "token" in data, "Login response missing token"
        assert data["email"] == "admin@firmafinder.com"
        
        print(f"PASS: Login works, got token for {data['email']}")
        return data["token"]


class TestSaveCompanyWithDateFields:
    """Test saving a company with establishment_date, phone, j_number from ANAF"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for authenticated requests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"identifier": "admin@firmafinder.com", "password": "Admin123!"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_save_company_with_anaf_data(self, auth_token):
        """Save a company with establishment_date, phone, j_number from search results"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First search to get a company with ANAF data
        search_response = requests.get(
            f"{BASE_URL}/api/search/caen/1812",
            params={"county": "40", "since_date": "2025-01-01"},
            timeout=90
        )
        assert search_response.status_code == 200
        search_data = search_response.json()
        
        # Find a company with establishment_date
        company_to_save = None
        for c in search_data["companies"]:
            if c.get("establishment_date"):
                company_to_save = c
                break
        
        assert company_to_save is not None, "No company with establishment_date found"
        
        # Save the company
        save_payload = {
            "company_name": company_to_save["company_name"],
            "cui": company_to_save["cui"],
            "address": company_to_save.get("address", ""),
            "county": company_to_save.get("county", ""),
            "caen_code": company_to_save.get("caen_code", "1812"),
            "caen_description": company_to_save.get("caen_description", ""),
            "source_url": company_to_save.get("source_url", ""),
            "status": "potential_lead",
            "establishment_date": company_to_save.get("establishment_date", ""),
            "phone": company_to_save.get("phone", ""),
            "j_number": company_to_save.get("j_number", ""),
        }
        
        save_response = requests.post(
            f"{BASE_URL}/api/companies",
            json=save_payload,
            headers=headers,
            timeout=10
        )
        assert save_response.status_code == 200
        saved_company = save_response.json()
        
        # Verify saved data includes establishment_date
        assert saved_company["establishment_date"] == company_to_save.get("establishment_date", "")
        assert saved_company["company_name"] == company_to_save["company_name"]
        
        print(f"PASS: Saved company {saved_company['company_name']} with establishment_date={saved_company['establishment_date']}")
        
        # Cleanup - delete the test company
        company_id = saved_company["id"]
        delete_response = requests.delete(
            f"{BASE_URL}/api/companies/{company_id}",
            headers=headers,
            timeout=10
        )
        assert delete_response.status_code == 200
        print(f"PASS: Cleaned up test company {company_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
