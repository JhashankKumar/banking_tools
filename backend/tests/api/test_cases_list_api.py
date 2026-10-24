import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.audit.models import AuditEvent
from app.modules.users.models import Role
from app.seed import seed
from tests.factories import auth_header, make_user

URL = "/api/v1/cases"


@pytest.fixture(autouse=True)
def seeded(db_session: Session) -> None:
    seed(db_session, demo_password="seed-password-for-tests")
    db_session.commit()


@pytest.fixture
def analyst(client: TestClient, db_session: Session) -> dict[str, str]:
    make_user(db_session, username="analyst.one", role=Role.ANALYST)
    return auth_header(client, "analyst.one")


def test_analyst_lists_cases(client: TestClient, analyst: dict[str, str]) -> None:
    response = client.get(URL, headers=analyst)

    assert response.status_code == 200
    body = response.json()
    assert body["page"] == {"total": 5, "limit": 50, "offset": 0}
    by_id = {c["id"]: c for c in body["data"]}
    assert by_id["FR-10482"] == {
        "id": "FR-10482",
        "title": "Rapid onward transfer — potential connected-funds pattern requiring review",
        "status": "open",
        "opened_at": "2026-09-15T05:00:00Z",
        "alert_count": 1,
        "transaction_count": 2,
        "is_synthetic": True,
    }
    assert by_id["FR-10485"]["transaction_count"] == 3
    opened = [c["opened_at"] for c in body["data"]]
    assert opened == sorted(opened, reverse=True)


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
def test_cases_list_pagination_bounds(
    client: TestClient, analyst: dict[str, str], params: dict[str, int]
) -> None:
    assert client.get(URL, params=params, headers=analyst).status_code == 422


def test_auditor_denied_case_list(client: TestClient, db_session: Session) -> None:
    make_user(db_session, username="auditor.one", role=Role.AUDITOR)

    assert client.get(URL, headers=auth_header(client, "auditor.one")).status_code == 403


def test_case_list_view_audited(
    client: TestClient, db_session: Session, analyst: dict[str, str]
) -> None:
    client.get(URL, headers=analyst)

    actions = db_session.scalars(select(AuditEvent.action)).all()
    assert "case.list.viewed" in actions
