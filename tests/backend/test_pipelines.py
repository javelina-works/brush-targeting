import pytest
import requests
import json
import time
from tests.test_configs import BASE_URL

# ✅ Helper function to make API calls
def make_request(method, endpoint, data=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}

    if method == "GET":
        response = requests.get(url, params=data)
    elif method == "POST":
        response = requests.post(url, headers=headers, json=data)
    elif method == "PATCH":
        response = requests.patch(url, headers=headers, json=data)
    elif method == "DELETE":
        response = requests.delete(url)
    else:
        raise ValueError("Invalid method")

    return response

@pytest.fixture
def pipeline():
    response = make_request("POST", "/pipelines", {"name": "Test Pipeline"})
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "Test Pipeline"
    pipeline_id = data["id"]

    yield pipeline_id

    # Cleanup
    time.sleep(0.5)
    make_request("DELETE", f"/pipelines/{pipeline_id}")

@pytest.fixture
def stage(pipeline):
    response = make_request("POST", f"/pipelines/{pipeline}/stages", {"name": "stage1", "function": "stage1"})
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    stage_id = data["id"]

    yield stage_id

    # Cleanup
    time.sleep(0.5)
    make_request("DELETE", f"/pipelines/{pipeline}/stages/{stage_id}")



def test_list_pipelines():
    response = make_request("GET", "/pipelines")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_add_stage(pipeline):
    response = make_request("POST", f"/pipelines/{pipeline}/stages", {"name": "stage2", "function": "stage2"})
    assert response.status_code == 201
    assert "id" in response.json()

def test_list_stages(pipeline, stage):
    """Ensures stages can be listed for a given pipeline."""
    response = make_request("GET", f"/pipelines/{pipeline}/stages")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0  # Ensure at least one stage is present
    assert "id" in data[0]
    assert "function" in data[0]

def test_update_stage(pipeline, stage):
    """Ensures a stage can be updated to a new function."""
    # Update the stage to use a different function
    response = make_request("PATCH", f"/pipelines/{pipeline}/stages/{stage}", {"name": "stage2", "function": "stage2"})
    assert response.status_code == 200
    new_stage = response.json()
    assert new_stage["id"] == stage
    assert new_stage["function"] == "stage2"

    # Fetch updated stages to verify the change
    response = make_request("GET", f"/pipelines/{pipeline}/stages")
    assert response.status_code == 200
    stages = response.json()
    updated_stage = next((s for s in stages if s["id"] == stage), None)
    assert updated_stage is not None
    assert updated_stage["function"] == "stage2"


# ✅ Test running a pipeline
# def test_run_pipeline(pipeline, stage):
#     response = make_request("POST", f"/pipelines/{pipeline}/run", "input_image")
#     assert response.status_code == 200
#     assert "result" in response.json()

# TODO: Test inserting a stage not at the end of the pipeline