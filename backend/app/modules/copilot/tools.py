"""Case-bound, read-only tools the copilot may call (docs/project/AI_AGENT_AND_SECURITY.md).

The server binds every tool to the case being viewed: no tool takes a case ID, so the model
cannot reach another case. Outputs name parties by ID only (no display labels or customer
attributes), give amounts as strings and times in IST, wrap free text as untrusted data, and
carry deterministic derivations so the model never does arithmetic.
"""

import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.pagination import PageParams
from app.core.permissions import Permission
from app.modules.alerts import service as alerts
from app.modules.cases import service as cases
from app.modules.copilot.provider import ToolSpec
from app.modules.detection.registry import get_rule
from app.modules.evidence.models import Evidence
from app.modules.graph import service as graph
from app.modules.graph.schemas import MoneyPathOut, TransactionEdgeOut
from app.modules.transactions import service as transactions
from app.modules.transactions.schemas import PartyRef
from app.modules.users.models import User

IST = ZoneInfo("Asia/Kolkata")
MAX_PAYLOAD_CHARS = 12_000
_CITABLE = re.compile(r"\b(?:EV-[A-Z0-9-]+|TX-\d+)\b")


@dataclass(frozen=True)
class ToolContext:
    session: Session
    case_id: str
    user: User


@dataclass(frozen=True)
class ToolResult:
    payload: dict[str, Any]
    record_ids: set[str]  # Citable IDs in structured fields (never from untrusted text).


def format_ist(at: datetime) -> str:
    local = at.astimezone(IST)
    return f"{local:%d %b %Y, %H:%M:%S} IST"


def format_elapsed(seconds: int) -> str:
    """Same wording as the UI: "5 m 28 s"."""
    minutes, rest = divmod(seconds, 60)
    if minutes == 0:
        return f"{rest} s"
    return f"{minutes} m" if rest == 0 else f"{minutes} m {rest} s"


def untrusted(text: str | None) -> dict[str, str] | None:
    """Source text is data for the model, never instructions."""
    return None if text is None else {"untrusted_text": text}


def _party(p: PartyRef) -> dict[str, str]:
    return {"type": p.type, "id": p.id}


def _edge(e: TransactionEdgeOut) -> dict[str, Any]:
    return {
        "transaction_id": e.transaction_id,
        "kind": e.kind,
        "source": _party(e.source),
        "destination": _party(e.destination),
        "amount": f"{e.amount:.2f}",
        "currency": e.currency,
        "occurred_at": format_ist(e.occurred_at),
        "status": e.status.value,
        "is_final": e.is_final,
        "reversed_by": e.reversed_by,
        "rail": e.rail,
        "reference": untrusted(e.reference),  # Source-system free text.
        "evidence_id": e.evidence_id,
    }


def _path(p: MoneyPathOut) -> dict[str, Any]:
    first, last = p.edges[0], p.edges[-1]
    same_currency = first.currency == last.currency
    difference: Decimal | None = first.amount - last.amount if same_currency else None
    return {
        "hops": p.hops,
        "is_cycle": p.is_cycle,
        "has_non_final_edges": p.has_non_final_edges,
        "contains_reversal": p.contains_reversal,
        "returned_by_reversal": p.returned_by_reversal,
        "started_at": format_ist(p.started_at),
        "ended_at": format_ist(p.ended_at),
        "elapsed": format_elapsed(p.elapsed_seconds),
        "amount_in": f"{first.amount:.2f}" if same_currency else None,
        "amount_out": f"{last.amount:.2f}" if same_currency else None,
        "amount_difference": f"{difference:.2f}" if difference is not None else None,
        "limitations": p.limitations,
        "edges": [{**_edge(e), "hop": e.hop} for e in p.edges],
    }


class NoArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MoneyPathArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    max_hops: int = Field(default=3, ge=1, le=5)
    window_hours: int = Field(default=24, ge=1, le=168)


class GraphArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    window_hours: int = Field(default=24, ge=1, le=168)


class RuleArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rule_id: str = Field(max_length=64)


def _case_summary(ctx: ToolContext, _: NoArgs) -> dict[str, Any]:
    case = cases.get_case(ctx.session, ctx.case_id)
    return {
        "id": case.id,
        "title": case.title,
        "status": case.status.value,
        "opened_at": format_ist(case.opened_at),
        "alert_ids": case.alert_ids,
        "transaction_count": case.transaction_count,
    }


def _alerts(ctx: ToolContext, _: NoArgs) -> dict[str, Any]:
    items, _total = alerts.list_alerts(
        ctx.session, PageParams(limit=20, offset=0), case_id=ctx.case_id, rule_id=None
    )
    if not items:
        return {"alerts": [], "note": "No alerts are recorded for this case."}
    return {
        "alerts": [
            {
                "id": a.id,
                "rule": {"id": a.rule.id, "version": a.rule.version, "title": a.rule.title},
                "entity": _party(a.entity),
                "trigger_transaction_id": a.trigger_transaction_id,
                "transaction_ids": a.transaction_ids,
                "triggered_at": format_ist(a.triggered_at),
                "explanation": untrusted(a.explanation),
                "metrics": a.metrics,
                # The rule window in the same words as answers use ("30 m").
                "window": (
                    format_elapsed(int(a.metrics["window_seconds"]))
                    if a.metrics.get("window_seconds", "").isdigit()
                    else None
                ),
                "evidence_id": a.evidence_id,
            }
            for a in items
        ]
    }


def _transactions(ctx: ToolContext, _: NoArgs) -> dict[str, Any]:
    items, total = transactions.list_case_transactions(
        ctx.session, ctx.case_id, PageParams(limit=100, offset=0)
    )
    return {
        "total": total,
        "transactions": [
            {
                "id": t.id,
                "source": _party(t.source),
                "destination": _party(t.destination),
                "amount": f"{t.amount:.2f}",
                "currency": t.currency,
                "occurred_at": format_ist(t.occurred_at),
                "status": t.status.value,
                "source_status": untrusted(t.source_status),  # Source systems' own values.
                "rail": t.rail,
                "reference": untrusted(t.reference),
                "description": untrusted(t.description),
                "reversal_of_transaction_id": t.reversal_of_transaction_id,
                "evidence_id": t.evidence_id,
            }
            for t in items
        ],
    }


def _money_paths(ctx: ToolContext, args: MoneyPathArgs) -> dict[str, Any]:
    result = graph.get_money_paths(
        ctx.session, ctx.case_id, max_hops=args.max_hops, window_hours=args.window_hours
    )
    return {
        "parameters": {"max_hops": args.max_hops, "window_hours": args.window_hours},
        "truncated": result.truncated,
        "paths": [_path(p) for p in result.paths],
    }


def _case_graph(ctx: ToolContext, args: GraphArgs) -> dict[str, Any]:
    result = graph.get_case_graph(ctx.session, ctx.case_id, window_hours=args.window_hours)
    return {
        "parameters": {"window_hours": args.window_hours},
        "truncated": result.truncated,
        # Node labels are display names: deliberately left out (parties by ID only).
        "nodes": [
            {
                "id": n.id,
                "type": n.type,
                "status": n.status,
                "is_case_party": n.is_case_party,
                "alert_ids": n.alert_ids,
            }
            for n in result.nodes
        ],
        "edges": [{**_edge(e), "in_case": e.in_case} for e in result.edges],
    }


def _evidence(ctx: ToolContext, _: NoArgs) -> dict[str, Any]:
    cases.ensure_case_exists(ctx.session, ctx.case_id)
    rows = ctx.session.scalars(
        select(Evidence).where(Evidence.case_id == ctx.case_id).order_by(Evidence.id)
    )
    return {
        "evidence": [
            {
                "id": e.id,
                "type": e.evidence_type.value,
                "label": e.label.value,
                "source_table": e.source_table,
                "source_record_id": e.source_record_id,
            }
            for e in rows
        ]
    }


def _rule(ctx: ToolContext, args: RuleArgs) -> dict[str, Any]:
    rule = get_rule(args.rule_id)
    if rule is None:
        return {"error": "No rule with that ID"}
    return {
        "id": rule.rule_id,
        "version": rule.version,
        "title": rule.title,
        "description": rule.description,
        "parameters": dict(rule.parameters),
        "false_positive_caveats": list(rule.false_positive_caveats),
    }


def _citable_ids(value: object) -> set[str]:
    if isinstance(value, dict):
        if "untrusted_text" in value:
            return set()
        return set().union(*(_citable_ids(v) for v in value.values()))  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
    if isinstance(value, list):
        return set().union(*(_citable_ids(v) for v in value))  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
    if isinstance(value, str):
        return set(_CITABLE.findall(value))
    return set()


def _capped(payload: dict[str, Any]) -> dict[str, Any]:
    """Drop trailing list items until the payload fits; mark it truncated."""
    lists = [k for k, v in payload.items() if isinstance(v, list)]
    while len(json.dumps(payload)) > MAX_PAYLOAD_CHARS and lists:
        key = max(lists, key=lambda k: len(json.dumps(payload[k])))
        items: list[Any] = payload[key]
        if len(items) <= 1:
            break
        payload = {**payload, key: items[:-1], "truncated": True}
    return payload


@dataclass(frozen=True)
class CopilotTool:
    name: str
    description: str
    args_model: type[BaseModel]
    permission: Permission
    run: Callable[[ToolContext, Any], dict[str, Any]]

    def call(self, ctx: ToolContext, args: Mapping[str, Any]) -> ToolResult:
        parsed = self.args_model.model_validate(dict(args))
        payload = _capped(self.run(ctx, parsed))
        return ToolResult(payload=payload, record_ids=_citable_ids(payload))

    def spec(self) -> ToolSpec:
        return ToolSpec(self.name, self.description, self.args_model.model_json_schema())


_ALL = [
    CopilotTool(
        "get_case_summary",
        "The case being viewed: title, status, opened time, alert IDs, transaction count.",
        NoArgs,
        Permission.CASE_READ,
        _case_summary,
    ),
    CopilotTool(
        "get_alert_details",
        "Alerts on this case: rule, triggering transaction, metrics, evidence ID.",
        NoArgs,
        Permission.ALERT_READ,
        _alerts,
    ),
    CopilotTool(
        "get_transactions",
        "This case's transactions with amounts, IST times, statuses and evidence IDs.",
        NoArgs,
        Permission.TRANSACTION_READ,
        _transactions,
    ),
    CopilotTool(
        "find_money_paths",
        "Time-ordered money paths from this case's transactions, with elapsed time and "
        "amount difference computed by the server.",
        MoneyPathArgs,
        Permission.TRANSACTION_READ,
        _money_paths,
    ),
    CopilotTool(
        "get_case_graph",
        "Parties (by ID) and transactions around this case within a time window.",
        GraphArgs,
        Permission.TRANSACTION_READ,
        _case_graph,
    ),
    CopilotTool(
        "get_evidence_records",
        "Citable evidence IDs for this case with their labels and source records.",
        NoArgs,
        Permission.EVIDENCE_READ,
        _evidence,
    ),
    CopilotTool(
        "get_rule",
        "A detection rule's description, parameters and false-positive caveats.",
        RuleArgs,
        Permission.ALERT_READ,
        _rule,
    ),
]
TOOLS: Mapping[str, CopilotTool] = {t.name: t for t in _ALL}


def tool_specs() -> list[ToolSpec]:
    return [t.spec() for t in _ALL]
