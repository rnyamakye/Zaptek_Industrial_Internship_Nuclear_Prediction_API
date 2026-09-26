from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_current_user
from app.db.models import User

client = TestClient(app)

def mock_get_current_user():
    return User(id=1, email="test@example.com", role="user")

app.dependency_overrides[get_current_user] = mock_get_current_user


def _create_sample_prediction():
    payload = {
        "enrichment_percent": 3.8,
        "fuel_density": 10.3,
        "moderator_density": 1.0,
    }
    return client.post("/predictions", json=payload)


def test_analytics_summary():
    _create_sample_prediction()
    resp = client.get("/analytics/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_predictions"] >= 1
    assert "status_breakdown" in body
    assert "avg_k_eff" in body


def test_analytics_trends():
    _create_sample_prediction()
    resp = client.get("/analytics/trends")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    if body:
        assert "date" in body[0]
        assert "count" in body[0]
