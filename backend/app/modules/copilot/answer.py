"""The copilot's answer format and the server-side checks that keep it grounded.

The model must answer with JSON in four sections. Before an answer is stored, the server
removes any citation that is not this case's evidence (or a transaction a tool returned in this
run) and reports any amount, time or elapsed value that does not appear in the tool results:
the model narrates, it never changes or computes facts.
"""

import json
import re
from collections.abc import Iterable, Sequence
from decimal import Decimal, InvalidOperation
from typing import Annotated, Literal, cast

from pydantic import BaseModel, Field, ValidationError

from app.modules.copilot.tools import ToolResult, format_elapsed

DECLINE_SUGGESTIONS = [
    "Trace where the funds went",
    "What is not established?",
    "Draft a case note",
]


class AnswerFormatError(Exception):
    """The model's reply is not the required JSON answer."""


MAX_ITEMS = 12
Line = Annotated[str, Field(max_length=600)]


class AnswerItem(BaseModel):
    text: Line
    citations: list[str] = Field(default_factory=lambda: [], max_length=8)


class CopilotAnswer(BaseModel):
    kind: Literal["answer", "decline"]
    records: list[AnswerItem] = Field(default_factory=lambda: [], max_length=MAX_ITEMS)
    calculated: list[AnswerItem] = Field(default_factory=lambda: [], max_length=MAX_ITEMS)
    not_established: list[Line] = Field(default_factory=lambda: [], max_length=MAX_ITEMS)
    next_checks: list[Line] = Field(default_factory=lambda: [], max_length=MAX_ITEMS)
    suggestions: list[Line] = Field(default_factory=lambda: [], max_length=4)
    steps: list[str] = Field(default_factory=lambda: [])  # Filled by the server only.


def decline_answer() -> CopilotAnswer:
    return CopilotAnswer(kind="decline", suggestions=list(DECLINE_SUGGESTIONS))


def parse_model_answer(content: str) -> CopilotAnswer:
    text = content.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL)
    if fenced:
        text = fenced.group(1)
    try:
        answer = CopilotAnswer.model_validate(json.loads(text))
    except (json.JSONDecodeError, ValidationError):
        raise AnswerFormatError("The answer was not valid JSON in the required format") from None
    return answer.model_copy(update={"steps": []})


# --- grounding of values -------------------------------------------------------------------

_AMOUNT = re.compile(
    r"(?:₹\s?|INR\s?|Rs\.?\s?)\d[\d,]*(?:\.\d{1,2})?"  # ₹48,500 · INR 48500.00 · Rs. 48500
    r"|\b\d[\d,]*(?:\.\d{1,2})?\s?(?:rupees|INR)\b"  # 48500 rupees
    r"|\b\d{1,3}(?:,\d{2,3})+(?:\.\d{2})?\b"  # 48,500 · 48,500.00
    r"|\b\d+\.\d{2}\b",  # 48500.00
    re.IGNORECASE,
)
_TIME = re.compile(r"\b(\d{2}):(\d{2})(?::(\d{2}))?\b")
_DATE = re.compile(r"\b(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (\d{4})\b")
_ELAPSED = re.compile(
    r"\b(\d+) m(?: (\d+) s)?\b|\b(\d+) minutes?(?: (\d+) seconds?)?\b|\b(\d+) seconds?\b"
)


def _amount_key(raw: str) -> str | None:
    digits = re.sub(r"[^\d.]", "", raw).strip(".")
    try:
        return f"amount:{Decimal(digits):.2f}"
    except InvalidOperation:
        return None


def _elapsed_key(match: re.Match[str]) -> str:
    minutes = int(match.group(1) or match.group(3) or 0)
    seconds = int(match.group(2) or match.group(4) or match.group(5) or 0)
    return f"elapsed:{format_elapsed(minutes * 60 + seconds)}"


def _values(text: str) -> list[tuple[str, str]]:
    """(raw text, normalised key) for every checkable value in `text`."""
    found: list[tuple[str, str]] = []
    for m in _AMOUNT.finditer(text):
        key = _amount_key(m.group(0))
        if key:
            found.append((m.group(0), key))
    for m in _TIME.finditer(text):
        hh_mm = f"{m.group(1)}:{m.group(2)}"
        found.append((m.group(0), f"time:{hh_mm}:{m.group(3)}" if m.group(3) else f"time:{hh_mm}"))
    found += [
        (m.group(0), f"date:{int(m.group(1))} {m.group(2)} {m.group(3)}")
        for m in _DATE.finditer(text)
    ]
    found += [(m.group(0), _elapsed_key(m)) for m in _ELAPSED.finditer(text)]
    return found


def _trusted_strings(value: object) -> list[str]:
    """Every string in a tool payload except record text marked as untrusted."""
    if isinstance(value, dict):
        mapping = cast(dict[str, object], value)
        if "untrusted_text" in mapping:
            return []
        return [s for v in mapping.values() for s in _trusted_strings(v)]
    if isinstance(value, list):
        return [s for v in cast(list[object], value) for s in _trusted_strings(v)]
    return [str(value)] if isinstance(value, str | int) else []


def collect_tool_values(results: Sequence[ToolResult]) -> set[str]:
    """Values an answer may quote. Untrusted record text never grounds a value."""
    keys: set[str] = set()
    for text in (t for r in results for t in _trusted_strings(r.payload)):
        for _, key in _values(text):
            keys.add(key)
            if key.startswith("time:") and key.count(":") == 3:
                keys.add(key.rsplit(":", 1)[0])  # 10:02:14 also grounds "10:02".
    return keys


def _texts(answer: CopilotAnswer) -> Iterable[str]:
    yield from (i.text for i in answer.records)
    yield from (i.text for i in answer.calculated)
    yield from answer.not_established
    yield from answer.next_checks
    yield from answer.suggestions


# Conclusions the records can never support (docs/banking-domain/AI_DOMAIN_GUARDRAILS.md).
# Negated forms ("not confirmed", "does not prove") deliberately do not match.
_CONCLUSION = re.compile(
    r"\bfraud (?:is|was|has been) (?:confirmed|proven|established)\b"
    r"|\bconfirm(?:s|ed)? (?:the |that )?fraud\b"
    r"|\bprov(?:es|ed|en) (?:that |the )?(?:fraud|intent|ownership|guilt)\b"
    r"|\b(?:is|are) (?:a |an )?(?:fraudsters?|criminals?|(?:money )?mules?)\b"
    r"|\bcommitted fraud\b",
    re.IGNORECASE,
)


def validate_answer(
    answer: CopilotAnswer,
    *,
    case_evidence_ids: set[str],
    run_record_ids: set[str],
    tool_values: set[str],
) -> tuple[CopilotAnswer, list[str]]:
    """Returns the answer with unverifiable citations removed, plus value problems."""
    allowed = case_evidence_ids | {i for i in run_record_ids if i.startswith("TX-")}

    def clean(items: list[AnswerItem], *, require_citation: bool) -> list[AnswerItem]:
        kept: list[AnswerItem] = []
        for item in items:
            citations = [c for c in item.citations if c in allowed]
            if citations or not require_citation:
                kept.append(item.model_copy(update={"citations": citations}))
        return kept

    cleaned = answer.model_copy(
        update={
            "records": clean(answer.records, require_citation=True),
            "calculated": clean(answer.calculated, require_citation=False),
        }
    )
    texts = list(_texts(cleaned))
    problems = [
        f"Wording not allowed (a conclusion the records cannot support): {m.group(0)}"
        for text in texts
        for m in _CONCLUSION.finditer(text)
    ]
    problems += [
        f"Value not found in the case records: {raw}"
        for text in texts
        for raw, key in _values(text)
        if key not in tool_values
    ]
    return cleaned, problems


# --- scope: fraud-signal analysis only -----------------------------------------------------

_CUSTOMER_INFO = re.compile(
    r"\bphone\b|\bmobile\b|\bcontact (?:number|details)\b|\be-?mail\b|\baddress\b"
    r"|\bdate of birth\b|\bdob\b|\bpan\b|\baadhaa?r\b|\bpassport\b|\bkyc\b"
    r"|\boccupation\b|\bincome\b|\bsalary\b"
    r"|\bname of (?:the )?(?:owner|customer|holder|account holder|person|beneficiary)\b"
    r"|\b(?:customer|owner|holder)'?s? name\b"
    r"|\bwho (?:is behind|owns|is the owner|controls)\b"
    r"|\bother accounts\b|\bbalance\b|\bfraudster\b"
    r"|\bis (?:he|she|they|this person|the customer|the owner|the holder) (?:a )?fraud",
    re.IGNORECASE,
)


def is_customer_info_request(question: str) -> bool:
    """True for questions about the customer as a person, which the copilot declines."""
    return _CUSTOMER_INFO.search(question) is not None
