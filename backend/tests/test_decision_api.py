from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_decision_endpoint():
    response = client.post(
        "/api/decision/evaluate",
        json={
            "project_id": "TEST-001",
            "prediction_date": "2011-01",
            "cost_probability": 0.70,
            "schedule_probability": 0.30,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["project_id"] == "TEST-001"
    assert data["risk_level"] == "HIGH"
    assert data["early_warning"] is True

    assert data["cost_risk"]["flagged"] is True
    assert data["schedule_risk"]["flagged"] is False
