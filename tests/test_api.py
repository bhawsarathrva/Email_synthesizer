import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"]["status"] == "connected"


def test_get_emails_endpoint():
    response = client.get("/emails?page=1&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "emails" in data
    assert "total" in data
    assert len(data["emails"]) <= 5


def test_get_single_email_endpoint():
    response = client.get("/emails/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert "subject" in data
    assert "body" in data


def test_classify_and_verify_yes_endpoint():
    email_id = 5
    # 1. Classify
    class_resp = client.post(f"/emails/{email_id}/classify")
    assert class_resp.status_code == 200
    class_data = class_resp.json()
    assert class_data["category"] in ["Payroll", "Benefits", "Tax"]
    assert class_data["requires_verification"] is True

    # 2. Verify with YES
    ver_resp = client.post(
        f"/emails/{email_id}/verify",
        json={"decision": "YES", "verified_by": "api_tester"}
    )
    assert ver_resp.status_code == 200
    ver_data = ver_resp.json()
    assert ver_data["verification_status"] == "approved"
    assert ver_data["verified_category"] == class_data["category"]


def test_classify_and_verify_no_endpoint():
    email_id = 6
    # 1. Classify
    class_resp = client.post(f"/emails/{email_id}/classify")
    assert class_resp.status_code == 200
    class_data = class_resp.json()

    # 2. Verify with NO and correction to 'Benefits'
    ver_resp = client.post(
        f"/emails/{email_id}/verify",
        json={
            "decision": "NO",
            "correct_category": "Benefits",
            "feedback": "Corrected by human supervisor via API",
            "verified_by": "supervisor_api"
        }
    )
    assert ver_resp.status_code == 200
    ver_data = ver_resp.json()
    assert ver_data["verification_status"] == "corrected"
    assert ver_data["verified_category"] == "Benefits"
    # Preserves original prediction
    assert ver_data["ai_category"] is not None


def test_statistics_endpoint():
    response = client.get("/statistics")
    assert response.status_code == 200
    data = response.json()
    assert "total_emails" in data
    assert "pending_verification" in data
    assert "approved" in data
    assert "corrected" in data


def test_evaluation_endpoint():
    response = client.get("/evaluation")
    assert response.status_code == 200
    data = response.json()
    assert "accuracy" in data
    assert "payroll" in data
    assert "benefits" in data
    assert "tax" in data
    assert "f1" in data["payroll"]
