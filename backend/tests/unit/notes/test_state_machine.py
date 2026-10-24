import pytest

from app.modules.cases.models import CaseStatus
from app.modules.notes.service import (
    CaseStatusConflictError,
    StatusEvent,
    extract_cited_ids,
    next_case_status,
)

OPEN, IN_REVIEW = CaseStatus.OPEN, CaseStatus.IN_REVIEW
ESCALATED, CLOSED = CaseStatus.ESCALATED, CaseStatus.CLOSED

ALLOWED: list[tuple[CaseStatus, StatusEvent, CaseStatus]] = [
    (OPEN, "submit", IN_REVIEW),
    (ESCALATED, "submit", ESCALATED),
    (IN_REVIEW, "return", OPEN),
    (ESCALATED, "return", ESCALATED),
    (IN_REVIEW, "approve_keep_open", OPEN),
    (ESCALATED, "approve_keep_open", ESCALATED),
    (IN_REVIEW, "approve_escalate", ESCALATED),
    (ESCALATED, "approve_escalate", ESCALATED),
    (IN_REVIEW, "approve_close", CLOSED),
    (ESCALATED, "approve_close", CLOSED),
    (ESCALATED, "close", CLOSED),
]
EVENTS: list[StatusEvent] = [
    "submit",
    "return",
    "approve_keep_open",
    "approve_escalate",
    "approve_close",
    "close",
]


@pytest.mark.parametrize(("current", "event", "expected"), ALLOWED)
def test_allowed_transitions(current: CaseStatus, event: StatusEvent, expected: CaseStatus) -> None:
    assert next_case_status(current, event) == expected


@pytest.mark.parametrize(
    ("current", "event"),
    [
        (status, event)
        for status in CaseStatus
        for event in EVENTS
        if (status, event) not in {(c, e) for c, e, _ in ALLOWED}
    ],
)
def test_everything_else_conflicts(current: CaseStatus, event: StatusEvent) -> None:
    with pytest.raises(CaseStatusConflictError):
        next_case_status(current, event)


def test_closed_is_final() -> None:
    for event in EVENTS:
        with pytest.raises(CaseStatusConflictError):
            next_case_status(CLOSED, event)


def test_extract_cited_ids_in_order_without_duplicates() -> None:
    body = "TX-1001 [EV-10482-TX-1001] then TX-1002 [EV-10482-TX-1002, EV-10482-TX-1001]"

    assert extract_cited_ids(body) == [
        "TX-1001",
        "EV-10482-TX-1001",
        "TX-1002",
        "EV-10482-TX-1002",
    ]
