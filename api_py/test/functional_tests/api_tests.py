import pytest
import requests
import pytest_asyncio

class TestAPI:
    url = "http://127.0.0.1:8000"
    # User hits base url
    def test_get_record_at_base_url(self):
        response: requests.Response = requests.get(self.url)
        assert(response is not None)
        assert(response.status_code == 404)
    
    # User gets health check
    
    def test_server_health_check(self):
        response : requests.Response = requests.get(self.url + '/api/v1/health')
        assert(response is not None)
        assert(200 == response.status_code)
    
    # User creates basic record with data
    async def test_create_record(self):
        data = {
            "company_name": "Test Inc",
            "company_id": 1,
            "policy_start_date": "01-01-2026",
            "policy_end_date": "07-31-2026",
            "update_cutoff_timestamp":"07-01-2026",
            "status":"ACTIVE"
        }
        response:requests.Response = requests.post(self.url + "/records", data=data)
        assert(response is not None)
        assert(response.status_code == 200)
        assert(response.content.get("company_id") == 1)
            
    # User wants to know the properties of a saved record
    async def test_get_record(self):
        pass
    
    # User forgets a change and resubmits a record with updated changes.
    async def test_update_record(self):
        pass
        
    # User wants to get the latest version of a record
    async def test_get_latest_version_of_record():
        pass
    
    # User wants to get historical view of a record
    async def test_get_historical_view_of_record():
        pass
    
    async def test_get_specific_version_of_record():
        pass
    
    # Record 1 extends from 01/01 to 07/31. Record 2 is an update to the policy from 03/01 to 07/31.
    # The original record date must still exist. The new record dates for Record 1 and Record 2 must stil be present. Hint: Link/Tree forking 
    async def test_reconcile_record_history():
        pass
    # Company updates the Record object and the user retrieves pre-update Record through newer api
    async def test_get_v1_record_via_v2_api(self):
        pass
    
    # User wants to compare a pre-update and a post-update record.
    async def test_compare_diff_records():
        pass
    
    # Company wants to migrate pre-update record to post-update record
    async def test_migrate_v1_record_to_v2():
        pass
    
    # Company wants to use a post-update record in a system that supports pre-update records
    async def test_migrate_v2_record_to_v1():
        pass

    # Company must update record coverage with 