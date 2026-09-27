from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_current_user
from app.db.models import User

client = TestClient(app)

def mock_get_current_user():
    return User(id=1, email="test@example.com", role="user")

app.dependency_overrides[get_current_user] = mock_get_current_user


def test_model_info():
    resp = client.get("/model/info")
    assert resp.status_code == 200
    body = resp.json()
    assert "model_loaded" in body
    assert "feature_names" in body
    assert "status_thresholds" in body
