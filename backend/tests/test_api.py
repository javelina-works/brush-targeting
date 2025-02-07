from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_create_project():
    response = client.post("/graphql", json={"query": "mutation { createProject(name: \"Ranch ABC\") { id name } }"})
    assert response.status_code == 200
    assert "Ranch ABC" in response.json()["data"]["createProject"]["name"]
