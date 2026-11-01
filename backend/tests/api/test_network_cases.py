"""Network cases FR-10489..FR-10493: several parties; alerts only where the rule's contract says."""

from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.cases.models import Alert, Case, case_transactions
from app.modules.users.models import Role
from app.seed import seed
from tests.factories import signed_in


@pytest.fixture(autouse=True)
def seeded(db_session: Session) -> None:
    seed(db_session, demo_password="seed-password-for-tests")
    db_session.commit()


@pytest.fixture
def analyst(client: TestClient, db_session: Session) -> dict[str, str]:
    return signed_in(client, db_session, Role.ANALYST)


def _linked(db_session: Session, case_id: str) -> list[str]:
    return sorted(
        db_session.scalars(
            select(case_transactions.c.transaction_id).where(case_transactions.c.case_id == case_id)
        )
    )


def _alerts(db_session: Session, case_id: str) -> dict[str, tuple[str, ...]]:
    alerts = db_session.scalars(select(Alert).where(Alert.case_id == case_id))
    return {a.id: tuple(a.transaction_ids) for a in alerts}


@pytest.mark.parametrize(
    ("case_id", "transactions", "alerts"),
    [
        (
            "FR-10489",
            [f"TX-890{i}" for i in range(1, 7)],
            {"AL-ROT-TX-8906": ("TX-8905", "TX-8906")},
        ),
        ("FR-10490", [f"TX-900{i}" for i in range(1, 7)], {}),
        (
            "FR-10491",
            ["TX-9101", "TX-9102", "TX-9103"],
            {
                "AL-ROT-TX-9102": ("TX-9101", "TX-9102"),
                "AL-ROT-TX-9103": ("TX-9102", "TX-9103"),
            },
        ),
        (
            "FR-10492",
            [f"TX-920{i}" for i in range(1, 7)],
            {"AL-ROT-TX-9204": ("TX-9202", "TX-9204")},
        ),
        ("FR-10493", ["TX-9301", "TX-9302"], {"AL-ROT-TX-9302": ("TX-9301", "TX-9302")}),
    ],
)
def test_network_case_records_and_alerts(
    db_session: Session, case_id: str, transactions: list[str], alerts: dict[str, Any]
) -> None:
    assert db_session.get(Case, case_id) is not None
    assert _linked(db_session, case_id) == transactions
    assert _alerts(db_session, case_id) == alerts


def test_three_hop_chain_is_one_money_path(client: TestClient, analyst: dict[str, str]) -> None:
    response = client.get("/api/v1/cases/FR-10491/money-paths", headers=analyst)

    assert response.status_code == 200, response.text
    [path] = response.json()["data"]["paths"]
    assert path["hops"] == 3
    assert [e["transaction_id"] for e in path["edges"]] == ["TX-9101", "TX-9102", "TX-9103"]


def test_fan_in_graph_shows_every_payer(client: TestClient, analyst: dict[str, str]) -> None:
    response = client.get("/api/v1/cases/FR-10489/graph", headers=analyst)

    assert response.status_code == 200, response.text
    nodes = {n["id"] for n in response.json()["data"]["nodes"]}
    assert nodes >= {"ACC-891", "ACC-892", "ACC-893", "ACC-894", "ACC-895", "BEN-M89", "ACC-X89"}
