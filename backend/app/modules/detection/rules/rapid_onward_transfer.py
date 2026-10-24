"""RAPID_ONWARD_TRANSFER v1: funds received and sent on soon after. A heuristic for review only."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal

from app.modules.detection.contract import RuleHit
from app.modules.detection.facts import TransactionFact, is_completed


def _default_thresholds() -> Mapping[str, Decimal]:
    return {"INR": Decimal("10000.00")}


@dataclass(frozen=True)
class RapidOnwardTransferConfig:
    window: timedelta = timedelta(minutes=30)
    min_onward_ratio: Decimal = Decimal("0.50")
    # Per-currency minimum incoming amount. A currency with no threshold is out of scope.
    min_incoming_amount: Mapping[str, Decimal] = field(default_factory=_default_thresholds)


def _plural(count: int, unit: str) -> str:
    return f"{count} {unit}" if count == 1 else f"{count} {unit}s"


def describe_elapsed(seconds: int) -> str:
    minutes, rest = divmod(seconds, 60)
    if minutes == 0:
        return _plural(rest, "second")
    if rest == 0:
        return _plural(minutes, "minute")
    return f"{_plural(minutes, 'minute')} {_plural(rest, 'second')}"


class RapidOnwardTransfer:
    rule_id: str = "RAPID_ONWARD_TRANSFER"
    version: str = "1"
    code: str = "ROT"
    title: str = "Rapid onward transfer"
    description: str = (
        "An account or beneficiary receives a completed transfer and sends a separate completed "
        "transfer onward, in the same currency, within the configured window, for at least the "
        "configured share of the amount received. Transfers back to the original sender are "
        "ignored."
    )
    required_fields: tuple[str, ...] = (
        "source",
        "destination",
        "amount",
        "currency",
        "occurred_at",
        "status",
        "reversal_of_transaction_id",
    )
    false_positive_caveats: tuple[str, ...] = (
        "Salary, payroll, or business accounts that routinely pass funds through.",
        "Payment aggregators and merchants settling onward to their own accounts.",
        "Family or household transfers made in quick succession.",
        "Records missing from the dataset (fees, other transfers, holds) may change the picture.",
    )

    def __init__(self, config: RapidOnwardTransferConfig | None = None) -> None:
        self.config = config or RapidOnwardTransferConfig()

    @property
    def parameters(self) -> Mapping[str, str]:
        thresholds = ",".join(
            f"{currency}:{amount:.2f}"
            for currency, amount in sorted(self.config.min_incoming_amount.items())
        )
        return {
            "window_seconds": str(int(self.config.window.total_seconds())),
            "min_onward_ratio": f"{self.config.min_onward_ratio:.2f}",
            "min_incoming_amount": thresholds,
        }

    def evaluate(self, facts: Sequence[TransactionFact]) -> list[RuleHit]:
        completed = sorted(
            (f for f in facts if is_completed(f)), key=lambda f: (f.occurred_at, f.id)
        )
        hits: list[RuleHit] = []
        # Quadratic scan: fine for demo-scale datasets; index by party before scaling up.
        for index, out in enumerate(completed):
            incoming = self._most_recent_qualifying_incoming(out, completed[:index])
            if incoming is not None:
                hits.append(self._hit(incoming, out))
        return hits

    def _most_recent_qualifying_incoming(
        self, out: TransactionFact, earlier: Sequence[TransactionFact]
    ) -> TransactionFact | None:
        candidate: TransactionFact | None = None
        for inc in reversed(earlier):
            if out.occurred_at - inc.occurred_at > self.config.window:
                break
            if inc.destination != out.source or inc.id == out.id:
                continue
            if inc.source == out.destination:
                # Money going back to anyone who just paid this party looks like a refund.
                return None
            if candidate is None and self._qualifies(inc, out):
                candidate = inc
        return candidate

    def _qualifies(self, inc: TransactionFact, out: TransactionFact) -> bool:
        threshold = self.config.min_incoming_amount.get(inc.currency)
        return (
            inc.reverses is None  # a reversal record returns funds; it is not new incoming money
            and inc.currency == out.currency
            and threshold is not None
            and inc.amount >= threshold
            and out.amount >= inc.amount * self.config.min_onward_ratio
        )

    def _hit(self, inc: TransactionFact, out: TransactionFact) -> RuleHit:
        elapsed = int((out.occurred_at - inc.occurred_at).total_seconds())
        entity_id = out.source[1]
        explanation = (
            f"{entity_id} received {inc.currency} {inc.amount:.2f} in {inc.id} and sent "
            f"{out.currency} {out.amount:.2f} in {out.id} {describe_elapsed(elapsed)} later. "
            "Signal for analyst review; not a finding of fraud."
        )
        return RuleHit(
            rule_id=self.rule_id,
            rule_version=self.version,
            rule_code=self.code,
            entity=out.source,
            trigger_transaction_id=out.id,
            transaction_ids=(inc.id, out.id),
            triggered_at=out.occurred_at,
            explanation=explanation,
            metrics={
                "elapsed_seconds": str(elapsed),
                "incoming_transaction_id": inc.id,
                "incoming_amount": f"{inc.amount:.2f}",
                "outgoing_transaction_id": out.id,
                "outgoing_amount": f"{out.amount:.2f}",
                "currency": out.currency,
                "window_seconds": str(int(self.config.window.total_seconds())),
                "min_onward_ratio": f"{self.config.min_onward_ratio:.2f}",
            },
        )
