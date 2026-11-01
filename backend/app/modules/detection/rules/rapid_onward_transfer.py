"""RAPID_ONWARD_TRANSFER v2: funds received and sent on soon after. A heuristic for review only.

v2 also compares transfers in different currencies, but only through a converted amount and
rate stated on one of the two records. No exchange rate is ever looked up or invented.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal

from app.modules.detection.contract import RuleHit
from app.modules.detection.facts import Conversion, TransactionFact, is_completed


def _default_thresholds() -> Mapping[str, Decimal]:
    return {"INR": Decimal("10000.00")}


@dataclass(frozen=True)
class RapidOnwardTransferConfig:
    window: timedelta = timedelta(minutes=30)
    min_onward_ratio: Decimal = Decimal("0.50")
    # Per-currency minimum incoming amount. A currency with no threshold is out of scope.
    min_incoming_amount: Mapping[str, Decimal] = field(default_factory=_default_thresholds)


@dataclass(frozen=True)
class _Comparison:
    """Both amounts in one currency; `converted` is the record whose stated conversion was used."""

    currency: str
    incoming: Decimal
    outgoing: Decimal
    converted: TransactionFact | None = None


def _compare(inc: TransactionFact, out: TransactionFact) -> _Comparison | None:
    if inc.currency == out.currency:
        return _Comparison(inc.currency, inc.amount, out.amount)
    if out.converted is not None and out.converted.currency == inc.currency:
        return _Comparison(inc.currency, inc.amount, out.converted.amount, out)
    if inc.converted is not None and inc.converted.currency == out.currency:
        return _Comparison(out.currency, inc.converted.amount, out.amount, inc)
    return None


def _rate(conversion: Conversion) -> str:
    return format(conversion.rate.normalize(), "f")


def _plural(count: int, unit: str) -> str:
    return f"{count} {unit}" if count == 1 else f"{count} {unit}s"


def describe_elapsed(seconds: int) -> str:
    """Wording like "5 minutes 28 seconds"; from one hour on, hours and minutes only."""
    if seconds >= 3600:
        hours, minutes = divmod(seconds // 60, 60)
        if minutes == 0:
            return _plural(hours, "hour")
        return f"{_plural(hours, 'hour')} {_plural(minutes, 'minute')}"
    minutes, rest = divmod(seconds, 60)
    if minutes == 0:
        return _plural(rest, "second")
    if rest == 0:
        return _plural(minutes, "minute")
    return f"{_plural(minutes, 'minute')} {_plural(rest, 'second')}"


class RapidOnwardTransfer:
    rule_id: str = "RAPID_ONWARD_TRANSFER"
    version: str = "2"
    code: str = "ROT"
    title: str = "Rapid onward transfer"
    description: str = (
        "An account or beneficiary receives a completed transfer and sends a separate completed "
        "transfer onward within the configured window, for at least the configured share of the "
        "amount received. Transfers in different currencies are compared only through the "
        "converted amount and rate stated on one of the two records. Transfers back to the "
        "original sender are ignored."
    )
    required_fields: tuple[str, ...] = (
        "source",
        "destination",
        "amount",
        "currency",
        "converted_amount, converted_currency, fx_rate (when currencies differ)",
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
        if inc.reverses is not None:  # a reversal record returns funds; it is not new money
            return False
        both = _compare(inc, out)
        if both is None:
            return False
        threshold = self.config.min_incoming_amount.get(both.currency)
        return (
            threshold is not None
            and both.incoming >= threshold
            and both.outgoing >= both.incoming * self.config.min_onward_ratio
        )

    @staticmethod
    def _amount(fact: TransactionFact, both: _Comparison) -> str:
        text = f"{fact.currency} {fact.amount:.2f}"
        if both.converted is fact and fact.converted is not None:
            c = fact.converted
            text += f" ({c.currency} {c.amount:.2f} at the recorded rate {_rate(c)})"
        return text

    def _hit(self, inc: TransactionFact, out: TransactionFact) -> RuleHit:
        both = _compare(inc, out)
        if both is None:  # unreachable: only pairs that qualified get here
            raise ValueError(f"{inc.id} and {out.id} cannot be compared")
        elapsed = int((out.occurred_at - inc.occurred_at).total_seconds())
        entity_id = out.source[1]
        explanation = (
            f"{entity_id} received {self._amount(inc, both)} in {inc.id} and sent "
            f"{self._amount(out, both)} in {out.id} {describe_elapsed(elapsed)} later. "
            "Signal for analyst review; not a finding of fraud."
        )
        metrics = {
            "elapsed_seconds": str(elapsed),
            "incoming_transaction_id": inc.id,
            "incoming_amount": f"{inc.amount:.2f}",
            "outgoing_transaction_id": out.id,
            "outgoing_amount": f"{out.amount:.2f}",
            "currency": both.currency,
        }
        if both.converted is not None and both.converted.converted is not None:
            conversion = both.converted.converted
            metrics |= {
                "incoming_currency": inc.currency,
                "outgoing_currency": out.currency,
                "converted_transaction_id": both.converted.id,
                "converted_amount": f"{conversion.amount:.2f}",
                "fx_rate": _rate(conversion),
            }
        return RuleHit(
            rule_id=self.rule_id,
            rule_version=self.version,
            rule_code=self.code,
            entity=out.source,
            trigger_transaction_id=out.id,
            transaction_ids=(inc.id, out.id),
            triggered_at=out.occurred_at,
            explanation=explanation,
            metrics=metrics
            | {
                "window_seconds": str(int(self.config.window.total_seconds())),
                "min_onward_ratio": f"{self.config.min_onward_ratio:.2f}",
            },
        )
