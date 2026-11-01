from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.users.models import Role
from tests.factories import auth_header, make_user


def test_rules_catalog_lists_all_rules(client: TestClient, db_session: Session) -> None:
    make_user(db_session, username="analyst.one", role=Role.ANALYST)

    response = client.get("/api/v1/rules", headers=auth_header(client, "analyst.one"))

    assert response.status_code == 200
    rules = response.json()["data"]
    assert [r["id"] for r in rules] == [
        "RAPID_ONWARD_TRANSFER",
        "FAN_OUT_SPLIT",
        "FAN_IN_COLLECT",
        "CIRCULAR_FLOW",
    ]
    rot, fos, fic, cir = rules
    assert (rot["version"], rot["code"], rot["title"]) == ("2", "ROT", "Rapid onward transfer")
    assert rot["false_positive_caveats"]
    assert "status" in rot["required_fields"]
    assert rot["parameters"] == {
        "window_seconds": "1800",
        "min_onward_ratio": "0.50",
        "min_incoming_amount": "INR:10000.00",
    }
    assert (fos["version"], fos["code"], fos["title"]) == ("1", "FOS", "Fan-out split")
    assert fos["parameters"] == {
        "window_seconds": "1800",
        "min_incoming_amount": "INR:50000.00",
        "min_transfers": "3",
        "min_onward_share": "0.80",
    }
    assert (fic["code"], cir["code"]) == ("FIC", "CIR")
    assert all(r["false_positive_caveats"] for r in rules)


def test_rules_require_alert_read(client: TestClient, db_session: Session) -> None:
    make_user(db_session, username="auditor.one", role=Role.AUDITOR)

    response = client.get("/api/v1/rules", headers=auth_header(client, "auditor.one"))

    assert response.status_code == 403
