from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.audit.models import AuditEvent
from app.modules.cases.models import Alert
from app.modules.graph.paths import (
    CYCLE,
    HOP_LIMIT,
    LIMITED_TO_DATASET,
    NON_FINAL,
    RETURNED_BY_REVERSAL,
    REVERSAL,
)
from app.modules.users.models import Role
from app.seed import seed
from tests.factories import assert_error, signed_in


def url(case_id: str) -> str:
    return f"/api/v1/cases/{case_id}/money-paths"


@pytest.fixture(autouse=True)
def seeded(db_session: Session) -> None:
    seed(db_session, demo_password="seed-password-for-tests")
    db_session.commit()


@pytest.fixture
def analyst(client: TestClient, db_session: Session) -> dict[str, str]:
    return signed_in(client, db_session, Role.ANALYST)


def paths_of(client: TestClient, headers: dict[str, str], case_id: str, **params: int) -> Any:
    response = client.get(url(case_id), params=params, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()["data"]


def edge_ids(path: Any) -> list[str]:
    return [e["transaction_id"] for e in path["edges"]]


def test_fr_10482_money_path_exact(client: TestClient, analyst: dict[str, str]) -> None:
    assert paths_of(client, analyst, "FR-10482") == {
        "case_id": "FR-10482",
        "parameters": {"max_hops": 3, "window_hours": 24},
        "truncated": False,
        "paths": [
            {
                "hops": 2,
                "is_cycle": False,
                "has_non_final_edges": False,
                "contains_reversal": False,
                "returned_by_reversal": False,
                "currencies": ["INR"],
                "started_at": "2026-09-15T04:32:14Z",
                "ended_at": "2026-09-15T04:37:42Z",
                "elapsed_seconds": 328,
                "limitations": [LIMITED_TO_DATASET],
                "edges": [
                    {
                        "hop": 1,
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
                        "evidence_id": "EV-10482-TX-1001",
                    },
                    {
                        "hop": 2,
                        "transaction_id": "TX-1002",
                        "kind": "transfer",
                        "source": {"type": "beneficiary", "id": "BEN-B"},
                        "destination": {"type": "account", "id": "ACC-C"},
                        "amount": "45000.00",
                        "currency": "INR",
                        "occurred_at": "2026-09-15T04:37:42Z",
                        "status": "settled",
                        "is_final": True,
                        "reversed_by": [],
                        "rail": "IMPS",
                        "reference": "SYN-REF-1002",
                        "evidence_id": "EV-10482-TX-1002",
                    },
                ],
            }
        ],
    }


def test_fr_10484_cycle_path(client: TestClient, analyst: dict[str, str]) -> None:
    [path] = paths_of(client, analyst, "FR-10484")["paths"]

    assert edge_ids(path) == ["TX-4001", "TX-4002", "TX-4003"]
    assert path["is_cycle"] is True
    assert CYCLE in path["limitations"]


def test_fr_10485_reversal_paths(client: TestClient, analyst: dict[str, str]) -> None:
    reversal_path, onward_path = paths_of(client, analyst, "FR-10485")["paths"]

    assert edge_ids(reversal_path) == ["TX-5001", "TX-5002"]
    assert edge_ids(onward_path) == ["TX-5001", "TX-5003"]
    original, reversal = reversal_path["edges"]
    assert original["is_final"] is False
    assert original["reversed_by"] == ["TX-5002"]
    assert (reversal["kind"], reversal["status"]) == ("reversal", "reversed")
    assert reversal_path["limitations"] == [
        LIMITED_TO_DATASET,
        NON_FINAL,
        REVERSAL,
        RETURNED_BY_REVERSAL,
    ]
    assert reversal_path["is_cycle"] is False
    assert reversal_path["returned_by_reversal"] is True


def test_max_hops_parameter_truncates(client: TestClient, analyst: dict[str, str]) -> None:
    data = paths_of(client, analyst, "FR-10484", max_hops=2)

    assert data["truncated"] is True
    assert data["parameters"] == {"max_hops": 2, "window_hours": 24}
    first = data["paths"][0]
    assert edge_ids(first) == ["TX-4001", "TX-4002"]
    assert HOP_LIMIT in first["limitations"]


def test_window_parameter_limits(client: TestClient, analyst: dict[str, str]) -> None:
    data = paths_of(client, analyst, "FR-10484", window_hours=3)

    assert all(len(p["edges"]) < 3 for p in data["paths"])


@pytest.mark.parametrize(
    "params", [{"max_hops": 0}, {"max_hops": 6}, {"window_hours": 0}, {"window_hours": 169}]
)
def test_parameter_bounds_422(
    client: TestClient, analyst: dict[str, str], params: dict[str, int]
) -> None:
    response = client.get(url("FR-10482"), params=params, headers=analyst)

    assert_error(response, 422, "VALIDATION_FAILED")


def test_unknown_case_404(client: TestClient, analyst: dict[str, str]) -> None:
    response = client.get(url("FR-99999"), headers=analyst)

    assert_error(response, 404, "CASE_NOT_FOUND")


def test_money_paths_require_auth(client: TestClient) -> None:
    assert client.get(url("FR-10482")).status_code == 401


def test_auditor_denied_money_paths_regardless_of_existence(
    client: TestClient, db_session: Session
) -> None:
    headers = signed_in(client, db_session, Role.AUDITOR)

    existing = client.get(url("FR-10482"), headers=headers)
    missing = client.get(url("FR-99999"), headers=headers)

    assert existing.status_code == missing.status_code == 403
    denied = db_session.scalars(
        select(AuditEvent).where(AuditEvent.action == "access.denied")
    ).all()
    assert len(denied) == 2


def test_money_paths_view_is_audited_with_parameters(
    client: TestClient, db_session: Session, analyst: dict[str, str]
) -> None:
    client.get(url("FR-10484"), params={"max_hops": 2}, headers=analyst)

    [event] = db_session.scalars(
        select(AuditEvent).where(AuditEvent.action == "case.money_paths.viewed")
    ).all()
    assert event.resource_id == "FR-10484"
    assert event.details == {
        "max_hops": "2",
        "window_hours": "24",
        "paths": "2",
        "truncated": "true",
    }


def test_fr_10484_cycle_raises_only_the_circular_flow_alert(db_session: Session) -> None:
    # Hops are hours apart, so RAPID_ONWARD_TRANSFER stays silent; CIRCULAR_FLOW catches the cycle.
    alerts = db_session.scalars(select(Alert.id).where(Alert.case_id == "FR-10484")).all()
    assert alerts == ["AL-CIR-TX-4003"]


def test_fact_load_is_row_limited(db_session: Session) -> None:
    """Review I1: transactions loaded for path search are capped; hitting the cap is reported."""
    from app.modules.graph.paths import BUDGET
    from app.modules.graph.service import get_money_paths

    result = get_money_paths(db_session, "FR-10484", max_hops=3, window_hours=24, max_facts=2)

    assert result.truncated is True
    assert all(BUDGET in p.limitations for p in result.paths)


def test_money_path_edges_include_rail_and_reference(
    client: TestClient, analyst: dict[str, str]
) -> None:
    [path] = paths_of(client, analyst, "FR-10482")["paths"]

    first = path["edges"][0]
    assert (first["rail"], first["reference"]) == ("IMPS", "SYN-REF-1001")
