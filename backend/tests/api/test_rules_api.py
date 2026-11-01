from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.users.models import Role
from tests.factories import auth_header, make_user


def test_rules_catalog_lists_rapid_onward_transfer(client: TestClient, db_session: Session) -> None:
    make_user(db_session, username="analyst.one", role=Role.ANALYST)

    response = client.get("/api/v1/rules", headers=auth_header(client, "analyst.one"))

    assert response.status_code == 200
    [rule] = response.json()["data"]
    assert rule["id"] == "RAPID_ONWARD_TRANSFER"
    assert (rule["version"], rule["code"], rule["title"]) == ("2", "ROT", "Rapid onward transfer")
    assert rule["false_positive_caveats"]
    assert "status" in rule["required_fields"]
    assert rule["parameters"] == {
        "window_seconds": "1800",
        "min_onward_ratio": "0.50",
        "min_incoming_amount": "INR:10000.00",
    }


def test_rules_require_alert_read(client: TestClient, db_session: Session) -> None:
    make_user(db_session, username="auditor.one", role=Role.AUDITOR)

    response = client.get("/api/v1/rules", headers=auth_header(client, "auditor.one"))

    assert response.status_code == 403
