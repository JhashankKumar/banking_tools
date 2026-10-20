import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.audit.models import AuditEvent
from app.modules.users.models import Role
from app.seed import seed
from tests.factories import auth_header, make_user

ALERTS_URL = "/api/v1/alerts"
ALERT_URL = "/api/v1/alerts/AL-ROT-TX-1002"


@pytest.fixture(autouse=True)
def seeded(db_session: Session) -> None:
    seed(db_session, demo_password="seed-password-for-tests")
    db_session.commit()


@pytest.fixture
def analyst(client: TestClient, db_session: Session) -> dict[str, str]:
    make_user(db_session, username="analyst.one", role=Role.ANALYST)
    return auth_header(client, "analyst.one")


@pytest.fixture
def auditor(client: TestClient, db_session: Session) -> dict[str, str]:
    make_user(db_session, username="auditor.one", role=Role.AUDITOR)
    return auth_header(client, "auditor.one")


def audit_actions(session: Session) -> list[str]:
    return list(session.scalars(select(AuditEvent.action).order_by(AuditEvent.id)).all())


def test_analyst_lists_alerts_with_envelope(client: TestClient, analyst: dict[str, str]) -> None:
    response = client.get(ALERTS_URL, headers=analyst)

    assert response.status_code == 200
    body = response.json()
    assert body["page"] == {"total": 1, "limit": 50, "offset": 0}
    assert [a["id"] for a in body["data"]] == ["AL-ROT-TX-1002"]


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({"case_id": "FR-10482"}, ["AL-ROT-TX-1002"]),
        ({"case_id": "FR-10483"}, []),
        ({"rule_id": "RAPID_ONWARD_TRANSFER"}, ["AL-ROT-TX-1002"]),
        ({"rule_id": "SOMETHING_ELSE"}, []),
    ],
)
def test_filter_alerts(
    client: TestClient, analyst: dict[str, str], params: dict[str, str], expected: list[str]
) -> None:
    response = client.get(ALERTS_URL, params=params, headers=analyst)

    assert [a["id"] for a in response.json()["data"]] == expected


def test_alert_detail_matches_rule_output(client: TestClient, analyst: dict[str, str]) -> None:
    response = client.get(ALERT_URL, headers=analyst)

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "id": "AL-ROT-TX-1002",
            "rule": {
                "id": "RAPID_ONWARD_TRANSFER",
                "version": "1",
                "title": "Rapid onward transfer",
            },
            "entity": {"type": "beneficiary", "id": "BEN-B"},
            "trigger_transaction_id": "TX-1002",
            "transaction_ids": ["TX-1001", "TX-1002"],
            "case_id": "FR-10482",
            "triggered_at": "2026-09-15T04:37:42Z",
            "explanation": (
                "BEN-B received INR 48500.00 in TX-1001 and sent INR 45000.00 in TX-1002 "
                "5 minutes 28 seconds later. Signal for analyst review; not a finding of fraud."
            ),
            "metrics": {
                "elapsed_seconds": "328",
                "incoming_transaction_id": "TX-1001",
                "incoming_amount": "48500.00",
                "outgoing_transaction_id": "TX-1002",
                "outgoing_amount": "45000.00",
                "currency": "INR",
                "window_seconds": "1800",
                "min_onward_ratio": "0.50",
            },
            "is_synthetic": True,
        }
    }


def test_alert_not_found_404_code(client: TestClient, analyst: dict[str, str]) -> None:
    response = client.get(f"{ALERTS_URL}/AL-NOPE", headers=analyst)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ALERT_NOT_FOUND"


@pytest.mark.parametrize("url", [ALERTS_URL, ALERT_URL, "/api/v1/rules"])
def test_alerts_and_rules_require_auth(client: TestClient, url: str) -> None:
    assert client.get(url).status_code == 401


def test_auditor_denied_alerts_regardless_of_existence(
    client: TestClient, db_session: Session, auditor: dict[str, str]
) -> None:
    existing = client.get(ALERT_URL, headers=auditor)
    missing = client.get(f"{ALERTS_URL}/AL-NOPE", headers=auditor)

    assert existing.status_code == missing.status_code == 403
    assert existing.json()["error"]["code"] == missing.json()["error"]["code"] == "AUTH_FORBIDDEN"
    assert audit_actions(db_session).count("access.denied") == 2


def test_alert_reads_are_audited(
    client: TestClient, db_session: Session, analyst: dict[str, str]
) -> None:
    client.get(ALERTS_URL, headers=analyst)
    client.get(ALERT_URL, headers=analyst)

    actions = audit_actions(db_session)
    assert "alert.list.viewed" in actions
    assert "alert.viewed" in actions


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
def test_alerts_pagination_bounds(
    client: TestClient, analyst: dict[str, str], params: dict[str, int]
) -> None:
    response = client.get(ALERTS_URL, params=params, headers=analyst)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"
