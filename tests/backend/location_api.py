import pytest
import requests
import json
import time
from tests.test_configs import BASE_URL


# ✅ Helper function to make API calls
def make_request(method, endpoint, data=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    print(data)
    print(json.dumps(data))
    
    if method == "GET":
        response = requests.get(url, params=data)
    elif method == "POST":
        response = requests.post(url, headers=headers, json=data)
    elif method == "PUT":
        response = requests.put(url, headers=headers, json=data)
    elif method == "DELETE":
        response = requests.delete(url)
    else:
        raise ValueError("Invalid method")
    
    return response


@pytest.fixture
def location():
    response = make_request("POST", "/locations/", {"name": "Test Ranch"})
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["name"] == "Test Ranch"
    location_id = data["id"]

    yield location_id # Pass location_id to our tests

    # Cleanup: delete location after the test
    time.sleep(0.5)
    delete_response = make_request("DELETE", f"/locations/{location_id}")
    assert delete_response.status_code in [200, 404] # 404 ok if already deleted

@pytest.fixture
def job(location):
    response = make_request("POST", "/jobs/", {"location_id": location, "name": "Test Job"})
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["name"] == "Test Job"
    assert data["location_id"] == location
    job_id =  data["id"]

    yield job_id # Pass job_id on to other tests

    # Cleanup: ensure we delete resources for test job
    time.sleep(0.5)
    delete_response = make_request("DELETE", f"/jobs/{job_id}")
    assert delete_response.status_code in [200, 404] # 404 ok if already deleted


# ✅ Test listing locations
def test_list_locations():
    response = make_request("GET", "/locations/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

# ✅ Test listing jobs
def test_list_jobs(location):
    response = make_request("GET", "/jobs/", {"location_id": location})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

# ✅ Test updating a location
def test_update_location(location):
    response = make_request("PUT", f"/locations/{location}", {"name": "Updated Test Ranch"})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == location
    assert data["name"] == "Updated Test Ranch"

# ✅ Test updating a job
def test_update_job(job, location):
    response = make_request("PUT", f"/jobs/{job}", {"name": "Updated Test Job", "location_id": location})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job
    assert data["name"] == "Updated Test Job"

# ✅ Test deleting a job
def test_delete_job(job, location):
    time.sleep(1)  # Ensure filesystem sync
    response = make_request("DELETE", f"/jobs/{job}")
    assert response.status_code == 200
    assert response.json()["message"] == "Job deleted"

    # Verify job no longer exists
    response = make_request("GET", "/jobs/", {"location_id": location})
    assert response.status_code == 200
    data = response.json()
    assert not any(job["id"] == job for job_entry in data)

# ✅ Test deleting a location
def test_delete_location(location):
    time.sleep(1)  # Ensure filesystem sync
    response = make_request("DELETE", f"/locations/{location}")
    assert response.status_code == 200
    assert response.json()["message"] == "Location deleted"

    # Verify location no longer exists
    response = make_request("GET", "/locations/")
    assert response.status_code == 200
    data = response.json()
    assert not any(loc["id"] == location for loc in data)
