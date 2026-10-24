from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.audit.models import AuditEvent
from app.modules.parties.models import Account, AccountStatus
from app.modules.transactions.models import Transaction, TransactionStatus
from app.modules.users.models import Role
from app.seed import seed
from tests.factories import auth_header, make_user

TX_1002_AT = datetime(2026, 9, 15, 4, 37, 42, tzinfo=UTC)


def url(case_id: str) -> str:
    return f"/api/v1/cases/{case_id}/graph"


@pytest.fixture(autouse=True)
def seeded(db_session: Session) -> None:
    seed(db_session, demo_password="seed-password-for-tests")
    db_session.commit()


@pytest.fixture
def analyst(client: TestClient, db_session: Session) -> dict[str, str]:
    make_user(db_session, username="analyst.one", role=Role.ANALYST)
    return auth_header(client, "analyst.one")


def graph_of(client: TestClient, headers: dict[str, str], case_id: str, **params: int) -> Any:
    response = client.get(url(case_id), params=params, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()["data"]


def add_account(session: Session, account_id: str) -> None:
    session.add(
        Account(
            id=account_id, status=AccountStatus.ACTIVE, currency="INR", scenario_id="test-graph"
        )
    )
    session.flush()


def add_transfer(
    session: Session,
    tx_id: str,
    source: str,
    destination: str,
    at: datetime,
    *,
    destination_is_beneficiary: bool = False,
) -> None:
    session.add(
        Transaction(
            id=tx_id,
            source_account_id=source,
            **(
                {"destination_beneficiary_id": destination}
                if destination_is_beneficiary
                else {"destination_account_id": destination}
            ),
            amount=Decimal("1000.00"),
            currency="INR",
            occurred_at=at,
            status=TransactionStatus.SETTLED,
            source_status="SUCCESS",
            scenario_id="test-graph",
        )
    )


def test_fr_10482_graph_exact(client: TestClient, analyst: dict[str, str]) -> None:
    data = graph_of(client, analyst, "FR-10482")

    assert data["case_id"] == "FR-10482"
    assert data["parameters"] == {"window_hours": 24}
    assert data["window"] == {"start": "2026-09-14T04:32:14Z", "end": "2026-09-16T04:37:42Z"}
    assert data["truncated"] is False
    assert data["nodes"] == [
        {
            "id": "ACC-001",
            "type": "account",
            "label": "Synthetic Customer One",
            "status": "active",
            "is_case_party": True,
            "alert_ids": [],
        },
        {
            "id": "ACC-C",
            "type": "account",
            "label": "ACC-C",
            "status": "active",
            "is_case_party": True,
            "alert_ids": [],
        },
        {
            "id": "BEN-B",
            "type": "beneficiary",
            "label": "Synthetic Beneficiary B",
            "status": None,
            "is_case_party": True,
            "alert_ids": ["AL-ROT-TX-1002"],
        },
    ]
    assert [e["transaction_id"] for e in data["edges"]] == ["TX-1001", "TX-1002"]
    assert data["edges"][0] == {
        "transaction_id": "TX-1001",
        "kind": "transfer",
        "source": {"type": "account", "id": "ACC-001"},
        "destination": {"type": "beneficiary", "id": "BEN-B"},
        "amount": "48500.00",
        "currency": "INR",
        "occurred_at": "2026-09-15T04:32:14Z",
        "status": "settled",
        "is_final": True,
        "reversed_by": [],
        "rail": "IMPS",
        "reference": "SYN-REF-1001",
        "in_case": True,
        "evidence_id": "EV-10482-TX-1001",
    }


def test_graph_includes_counterparty_transactions_in_window(
    client: TestClient, db_session: Session, analyst: dict[str, str]
) -> None:
    add_account(db_session, "ACC-OUT")
    add_transfer(db_session, "TX-G1", "ACC-C", "ACC-OUT", TX_1002_AT + timedelta(hours=2))
    add_transfer(db_session, "TX-G2", "ACC-C", "ACC-OUT", TX_1002_AT + timedelta(hours=30))
    db_session.commit()

    data = graph_of(client, analyst, "FR-10482")

    assert [e["transaction_id"] for e in data["edges"]] == ["TX-1001", "TX-1002", "TX-G1"]
    outside = data["edges"][2]
    assert (outside["in_case"], outside["evidence_id"]) == (False, None)
    [out_node] = [n for n in data["nodes"] if n["id"] == "ACC-OUT"]
    assert out_node["is_case_party"] is False


def test_graph_reversal_edge_labelled(client: TestClient, analyst: dict[str, str]) -> None:
    edges = {e["transaction_id"]: e for e in graph_of(client, analyst, "FR-10485")["edges"]}

    assert edges["TX-5002"]["kind"] == "reversal"
    assert edges["TX-5001"]["is_final"] is False
    assert edges["TX-5001"]["reversed_by"] == ["TX-5002"]


def test_graph_edge_cap_truncates(
    client: TestClient, db_session: Session, analyst: dict[str, str]
) -> None:
    add_account(db_session, "ACC-BUSY")
    start = datetime(2026, 9, 14, 5, 0, 0, tzinfo=UTC)
    for n in range(250):
        add_transfer(
            db_session,
            f"TX-B{n:03d}",
            "ACC-BUSY",
            "BEN-B",
            start + timedelta(minutes=n),
            destination_is_beneficiary=True,
        )
    db_session.commit()

    data = graph_of(client, analyst, "FR-10482")

    ids = [e["transaction_id"] for e in data["edges"]]
    assert len(ids) == 200
    assert {"TX-1001", "TX-1002"} <= set(ids)
    assert data["truncated"] is True


@pytest.mark.parametrize("hours", [0, 169])
def test_graph_window_bounds_422(client: TestClient, analyst: dict[str, str], hours: int) -> None:
    response = client.get(url("FR-10482"), params={"window_hours": hours}, headers=analyst)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"


def test_graph_unknown_case_404(client: TestClient, analyst: dict[str, str]) -> None:
    response = client.get(url("FR-99999"), headers=analyst)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CASE_NOT_FOUND"


def test_graph_requires_auth(client: TestClient) -> None:
    assert client.get(url("FR-10482")).status_code == 401


def test_auditor_denied_graph_regardless_of_existence(
    client: TestClient, db_session: Session
) -> None:
    make_user(db_session, username="auditor.one", role=Role.AUDITOR)
    headers = auth_header(client, "auditor.one")

    assert client.get(url("FR-10482"), headers=headers).status_code == 403
    assert client.get(url("FR-99999"), headers=headers).status_code == 403
    denied = db_session.scalars(
        select(AuditEvent).where(AuditEvent.action == "access.denied")
    ).all()
    assert len(denied) == 2


def test_graph_view_is_audited(
    client: TestClient, db_session: Session, analyst: dict[str, str]
) -> None:
    client.get(url("FR-10482"), headers=analyst)

    [event] = db_session.scalars(
        select(AuditEvent).where(AuditEvent.action == "case.graph.viewed")
    ).all()
    assert event.resource_id == "FR-10482"
    assert event.details == {"window_hours": "24", "nodes": "3", "edges": "2", "truncated": "false"}


def test_busy_counterparty_does_not_crowd_out_onward_transfers(
    client: TestClient, db_session: Session, analyst: dict[str, str]
) -> None:
    """Review I3: edges closest in time to the case's transactions are kept first."""
    add_account(db_session, "ACC-BUSY")
    add_account(db_session, "ACC-OUT")
    start = datetime(2026, 9, 14, 5, 0, 0, tzinfo=UTC)
    for n in range(250):
        add_transfer(
            db_session,
            f"TX-B{n:03d}",
            "ACC-BUSY",
            "BEN-B",
            start + timedelta(minutes=n),
            destination_is_beneficiary=True,
        )
    add_transfer(db_session, "TX-ONWARD", "ACC-C", "ACC-OUT", TX_1002_AT + timedelta(hours=1))
    db_session.commit()

    data = graph_of(client, analyst, "FR-10482")

    ids = [e["transaction_id"] for e in data["edges"]]
    assert "TX-ONWARD" in ids
    assert len(ids) == 200
    assert data["truncated"] is True


def test_graph_edges_include_rail_and_reference(
    client: TestClient, analyst: dict[str, str]
) -> None:
    edges = {e["transaction_id"]: e for e in graph_of(client, analyst, "FR-10482")["edges"]}

    assert (edges["TX-1002"]["rail"], edges["TX-1002"]["reference"]) == ("IMPS", "SYN-REF-1002")
