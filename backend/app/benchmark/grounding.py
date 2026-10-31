"""Scores the answer validator: faithful answers must pass, tampered ones must be caught."""

from collections.abc import Callable, Sequence
from typing import Any

from app.benchmark.families import Variant
from app.modules.copilot.answer import (
    AnswerItem,
    CopilotAnswer,
    collect_tool_values,
    validate_answer,
)
from app.modules.copilot.tools import ToolResult
from app.modules.detection.facts import TransactionFact

Tamper = Callable[[CopilotAnswer, Variant], CopilotAnswer]


def _evidence_id(fact: TransactionFact) -> str:
    return f"EV-B-{fact.id}"


def _faithful(v: Variant) -> CopilotAnswer:
    path = [f for f in v.facts if f.id in next(iter(v.expected_paths))]
    return CopilotAnswer(
        kind="answer",
        records=[
            AnswerItem(text=f"{f.id} moved INR {f.amount:.2f}.", citations=[_evidence_id(f)])
            for f in path
        ],
        not_established=["Who controls the receiving accounts."],
    )


def _tool_result(v: Variant) -> ToolResult:
    payload = {"transactions": [{"id": f.id, "amount": f"{f.amount:.2f}"} for f in v.facts]}
    return ToolResult(payload=payload, record_ids={f.id for f in v.facts})


def _fabricated_citation(a: CopilotAnswer, v: Variant) -> CopilotAnswer:
    first = a.records[0].model_copy(update={"citations": ["EV-B-INVENTED"]})
    return a.model_copy(update={"records": [first, *a.records[1:]]})


def _changed_value(a: CopilotAnswer, v: Variant) -> CopilotAnswer:
    fact = v.facts[0]
    text = f"{fact.id} moved INR {fact.amount + 1:.2f}."
    first = a.records[0].model_copy(update={"text": text})
    return a.model_copy(update={"records": [first, *a.records[1:]]})


def _unknown_id(a: CopilotAnswer, v: Variant) -> CopilotAnswer:
    return a.model_copy(update={"not_established": ["Whether TX-899999999 is linked."]})


def _conclusion(a: CopilotAnswer, v: Variant) -> CopilotAnswer:
    return a.model_copy(update={"not_established": ["Nothing: fraud is confirmed."]})


TAMPERS: dict[str, Tamper] = {
    "fabricated_citation": _fabricated_citation,
    "changed_value": _changed_value,
    "unknown_id": _unknown_id,
    "conclusion_wording": _conclusion,
}


def _caught(answer: CopilotAnswer, v: Variant) -> bool:
    """Rejected, or changed by the validator (an unverifiable citation removed)."""
    cleaned, problems = validate_answer(
        answer,
        case_evidence_ids={_evidence_id(f) for f in v.facts},
        run_record_ids={f.id for f in v.facts},
        tool_values=collect_tool_values([_tool_result(v)]),
    )
    return bool(problems) or cleaned != answer


def score_grounding(variants: Sequence[Variant]) -> dict[str, Any]:
    """One faithful and one of each tampered answer per variant that has a money path."""
    scored = [v for v in variants if v.expected_paths]
    false_rejections = sum(_caught(_faithful(v), v) for v in scored)
    tampered: dict[str, dict[str, Any]] = {}
    for kind, tamper in TAMPERS.items():
        caught = sum(_caught(tamper(_faithful(v), v), v) for v in scored)
        tampered[kind] = {
            "answers": len(scored),
            "rejected": caught,
            "rejection_rate": round(caught / len(scored), 4) if scored else None,
        }
    return {
        "faithful": {
            "answers": len(scored),
            "false_rejections": false_rejections,
            "false_rejection_rate": round(false_rejections / len(scored), 4) if scored else None,
        },
        "tampered": tampered,
    }
