import json

import pytest

from app.modules.copilot.answer import (
    AnswerFormatError,
    AnswerItem,
    CopilotAnswer,
    collect_tool_values,
    decline_answer,
    is_customer_info_request,
    parse_model_answer,
    validate_answer,
)
from app.modules.copilot.tools import ToolResult

CASE_EVIDENCE = {"EV-10482-TX-1001", "EV-10482-TX-1002", "EV-10482-AL-ROT-TX-1002"}
TOOL_VALUES = collect_tool_values(
    [
        ToolResult(
            payload={
                "paths": [
                    {
                        "elapsed": "5 m 28 s",
                        "amount_difference": "3500.00",
                        "edges": [
                            {"amount": "48500.00", "occurred_at": "15 Sep 2026, 10:02:14 IST"},
                            {"amount": "45000.00", "occurred_at": "15 Sep 2026, 10:07:42 IST"},
                        ],
                    }
                ]
            },
            record_ids={"TX-1001", "TX-1002", "TX-9001"},
        )
    ]
)


def _answer(*records: AnswerItem) -> CopilotAnswer:
    return CopilotAnswer(kind="answer", records=list(records))


def _validate(answer: CopilotAnswer) -> tuple[CopilotAnswer, list[str]]:
    return validate_answer(
        answer,
        case_evidence_ids=CASE_EVIDENCE,
        run_record_ids={"TX-1001", "TX-1002", "TX-9001"},
        tool_values=TOOL_VALUES,
    )


def test_parse_model_answer_accepts_fenced_json_and_ignores_model_steps() -> None:
    content = '```json\n{"kind": "answer", "records": [], "steps": ["made up"]}\n```'

    answer = parse_model_answer(content)

    assert answer.kind == "answer"
    assert answer.steps == []


def test_parse_model_answer_rejects_prose() -> None:
    with pytest.raises(AnswerFormatError):
        parse_model_answer("The money went to ACC-C.")


def test_foreign_citations_stripped() -> None:
    answer = _answer(
        AnswerItem(text="TX-1001 sent funds.", citations=["EV-10482-TX-1001", "EV-10483-TX-3001"]),
        AnswerItem(text="Another case's record.", citations=["EV-10483-TX-3001"]),
    )

    cleaned, _ = _validate(answer)

    assert [i.citations for i in cleaned.records] == [["EV-10482-TX-1001"]]


def test_tx_citation_allowed_only_if_returned_this_run() -> None:
    answer = _answer(
        AnswerItem(text="Onward hop outside the case.", citations=["TX-9001"]),
        AnswerItem(text="Never retrieved.", citations=["TX-7777"]),
    )

    cleaned, _ = _validate(answer)

    assert [i.citations for i in cleaned.records] == [["TX-9001"]]


def test_changed_amount_reported() -> None:
    answer = _answer(AnswerItem(text="ACC-001 sent ₹48,000.00.", citations=["EV-10482-TX-1001"]))

    _, problems = _validate(answer)

    assert problems == ["Value not found in the case records: ₹48,000.00"]


def test_matching_values_pass() -> None:
    answer = CopilotAnswer(
        kind="answer",
        records=[
            AnswerItem(
                text="ACC-001 sent ₹48,500.00 at 10:02:14 IST; BEN-B sent INR 45000.00 on.",
                citations=["EV-10482-TX-1001", "EV-10482-TX-1002"],
            )
        ],
        calculated=[
            AnswerItem(
                text="Sent on 5 m 28 s (5 minutes 28 seconds) later; ₹3,500.00 less.",
                citations=["EV-10482-TX-1001", "EV-10482-TX-1002"],
            )
        ],
    )

    _, problems = _validate(answer)

    assert problems == []


@pytest.mark.parametrize(
    "question",
    [
        "What is the phone number of the person behind ACC-001?",
        "Give me the customer's address",
        "who owns BEN-B",
        "Is this person a fraudster?",
        "what is the balance of ACC-C",
        "Share the email and date of birth of the account holder",
        "What is the name of the customer?",
        "Show the KYC documents and PAN",
        "Which other accounts does this customer hold?",
    ],
)
def test_customer_info_detected(question: str) -> None:
    assert is_customer_info_request(question)


@pytest.mark.parametrize(
    "question",
    [
        "Where did the money go after ACC-001?",
        "Why did the alert fire?",
        "Draft a case note",
        "What is not established?",
        "Could this be a benign transfer?",
        "How long between TX-1001 and TX-1002?",
    ],
)
def test_signal_questions_not_flagged(question: str) -> None:
    assert not is_customer_info_request(question)


def test_decline_answer_copy() -> None:
    answer = decline_answer()

    assert answer.kind == "decline"
    assert answer.records == []
    assert answer.suggestions == [
        "Trace where the funds went",
        "What is not established?",
        "Draft a case note",
    ]


def _problems_for(text: str, payload: dict[str, object]) -> list[str]:
    _, problems = validate_answer(
        _answer(AnswerItem(text=text, citations=["EV-10482-TX-1001"])),
        case_evidence_ids=CASE_EVIDENCE,
        run_record_ids=set(),
        tool_values=collect_tool_values([ToolResult(payload=payload, record_ids=set())]),
    )
    return problems


PAYLOAD: dict[str, object] = {
    "amount": "48500.00",
    "occurred_at": "15 Sep 2026, 10:02:14 IST",
    "window": "30 m",
}


@pytest.mark.parametrize(
    "text",
    [
        "ACC-001 moved 49500 rupees.",
        "BEN-B sent Rs. 98500 on.",
        "It happened at 10:03.",
        "Recorded on 25 Oct 2026.",
    ],
)
def test_changed_values_in_other_forms_are_reported(text: str) -> None:
    assert _problems_for(text, PAYLOAD) != []


@pytest.mark.parametrize(
    "text",
    [
        "ACC-001 moved 48500 rupees.",
        "ACC-001 moved Rs. 48,500.00 at 10:02 on 15 Sep 2026.",
        "The rule window is 30 minutes.",
    ],
)
def test_same_values_in_other_forms_pass(text: str) -> None:
    assert _problems_for(text, PAYLOAD) == []


# Models often write non-breaking spaces and hyphens ("5\u202fm", "TX\u20114242").
@pytest.mark.parametrize(
    "text",
    [
        "It took 9\u202fminutes.",
        "Sent on 6\u00a0m 28\u00a0s later.",
        "TX\u20114242 also moved money.",
        "See EV\u201199999\u2011X1.",
    ],
)
def test_non_ascii_spaces_and_hyphens_do_not_hide_values(text: str) -> None:
    assert _problems_for(text, PAYLOAD) != []


def test_non_ascii_spaces_and_hyphens_still_match_real_values() -> None:
    assert (
        _problems_for(
            "EV\u201110482\u2011TX\u20111001: the rule window is 30\u202fminutes.", PAYLOAD
        )
        == []
    )


def test_values_inside_untrusted_text_do_not_ground_an_answer() -> None:
    payload: dict[str, object] = {"description": {"untrusted_text": "Pay 99999.00 now"}}

    assert _problems_for("ACC-001 moved ₹99,999.00.", payload) != []


@pytest.mark.parametrize(
    "text",
    [
        "Fraud is confirmed for this case.",
        "This confirms fraud by ACC-001.",
        "ACC-001 is a money mule.",
        "BEN-B is a fraudster.",
        "The timing proves intent.",
    ],
)
def test_conclusion_wording_is_a_problem(text: str) -> None:
    answer = CopilotAnswer(kind="answer", next_checks=[text])

    _, problems = validate_answer(
        answer, case_evidence_ids=CASE_EVIDENCE, run_record_ids=set(), tool_values=set()
    )

    assert problems and problems[0].startswith("Wording not allowed")


@pytest.mark.parametrize(
    "text",
    [
        "The records do not establish fraud, ownership or intent.",
        "Signal for review; not a finding of fraud.",
        "Fraud is not confirmed by these records.",
    ],
)
def test_neutral_wording_passes(text: str) -> None:
    answer = CopilotAnswer(kind="answer", not_established=[text])

    _, problems = validate_answer(
        answer, case_evidence_ids=CASE_EVIDENCE, run_record_ids=set(), tool_values=set()
    )

    assert problems == []


def test_free_text_lists_are_bounded() -> None:
    too_many = json.dumps({"kind": "answer", "not_established": ["x"] * 13})
    too_long = json.dumps({"kind": "answer", "next_checks": ["x" * 601]})

    for content in (too_many, too_long):
        with pytest.raises(AnswerFormatError):
            parse_model_answer(content)


def test_record_ids_in_text_must_be_citable() -> None:
    answer = CopilotAnswer(
        kind="answer",
        not_established=[
            "TX-1001 and EV-10482-TX-1001 match; TX-4242 does not.",
            "Whether EV-99999-X1 exists.",
        ],
    )

    _, problems = _validate(answer)

    assert problems == [
        "Record ID not found in the case records: TX-4242",
        "Record ID not found in the case records: EV-99999-X1",
    ]


def test_case_transactions_may_be_named_without_a_tool_result() -> None:
    answer = _answer(AnswerItem(text="TX-1003 is on the case.", citations=["EV-10482-TX-1001"]))

    _, problems = validate_answer(
        answer,
        case_evidence_ids=CASE_EVIDENCE,
        run_record_ids=set(),
        tool_values=set(),
        case_transaction_ids=frozenset({"TX-1003"}),
    )

    assert problems == []
