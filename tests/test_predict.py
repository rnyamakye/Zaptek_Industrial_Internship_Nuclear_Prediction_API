from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_current_user
from app.db.models import User

client = TestClient(app)

def mock_get_current_user():
    return User(id=1, email="test@example.com", role="user")

app.dependency_overrides[get_current_user] = mock_get_current_user

def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200


def test_predict_valid_input():
    payload = {
        "enrichment_percent": 4.5,
        "fuel_density": 10.2,
        "moderator_density": 0.98,
    }
    resp = client.post("/predictions", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert "k_eff" in body
    assert "reactor_status" in body


def test_predict_invalid_input():
    payload = {"enrichment_percent": -5, "fuel_density": 10.2, "moderator_density": 0.98}
    resp = client.post("/predictions", json=payload)
    assert resp.status_code == 422
