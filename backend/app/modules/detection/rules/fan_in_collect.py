"""FAN_IN_COLLECT v1: several payers pay one party, which soon sends the money on. Review only."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import timedelta
from decimal import ROUND_DOWN, Decimal

from app.modules.detection.contract import RuleHit
from app.modules.detection.facts import TransactionFact, amount_in, is_completed
from app.modules.detection.rules.rapid_onward_transfer import describe_elapsed

_CENT = Decimal("0.01")
SIGNAL = "Signal for analyst review; not a finding of fraud."


def _default_thresholds() -> Mapping[str, Decimal]:
    return {"INR": Decimal("25000.00")}


@dataclass(frozen=True)
class FanInCollectConfig:
    window: timedelta = timedelta(minutes=30)
    min_payers: int = 3
    # Per-currency minimum combined incoming amount. A currency with no threshold is out of scope.
    min_total_incoming: Mapping[str, Decimal] = field(default_factory=_default_thresholds)
    min_onward_ratio: Decimal = Decimal("0.50")


class FanInCollect:
    rule_id: str = "FAN_IN_COLLECT"
    version: str = "1"
    code: str = "FIC"
    title: str = "Fan-in collect"
    description: str = (
        "An account or beneficiary sends a completed transfer after receiving completed transfers "
        "from at least the configured number of different payers within the configured window "
        "before it, together at least the configured amount, and the transfer sent is at least "
        "the configured share of what was received. Amounts are compared in the outgoing "
        "transfer's currency; incoming transfers in another currency count only through the "
        "converted amount stated on the record. A transfer to one of the payers is ignored."
    )
    required_fields: tuple[str, ...] = (
        "source",
        "destination",
        "amount",
        "currency",
        "converted_amount, converted_currency (when currencies differ)",
        "occurred_at",
        "status",
        "reversal_of_transaction_id",
    )
    false_positive_caveats: tuple[str, ...] = (
        "Merchants and payment aggregators settling collected payments.",
        "Group collections such as shared rent, events or savings groups.",
        "Business receivables swept to an operating account.",
        "Records missing from the dataset (fees, other transfers, holds) may change the picture.",
    )

    def __init__(self, config: FanInCollectConfig | None = None) -> None:
        self.config = config or FanInCollectConfig()

    @property
    def parameters(self) -> Mapping[str, str]:
        thresholds = ",".join(
            f"{currency}:{amount:.2f}"
            for currency, amount in sorted(self.config.min_total_incoming.items())
        )
        return {
            "window_seconds": str(int(self.config.window.total_seconds())),
            "min_payers": str(self.config.min_payers),
            "min_total_incoming": thresholds,
            "min_onward_ratio": f"{self.config.min_onward_ratio:.2f}",
        }

    def evaluate(self, facts: Sequence[TransactionFact]) -> list[RuleHit]:
        completed = sorted(
            (f for f in facts if is_completed(f) and f.reverses is None),
            key=lambda f: (f.occurred_at, f.id),
        )
        hits: list[RuleHit] = []
        for index, out in enumerate(completed):
            hit = self._collected_before(out, completed[:index])
            if hit is not None:
                hits.append(hit)
        return hits

    def _collected_before(
        self, out: TransactionFact, earlier: Sequence[TransactionFact]
    ) -> RuleHit | None:
        threshold = self.config.min_total_incoming.get(out.currency)
        if threshold is None:
            return None
        counted: list[tuple[TransactionFact, Decimal]] = []
        for inc in reversed(earlier):
            if out.occurred_at - inc.occurred_at > self.config.window:
                break
            if inc.destination != out.source:
                continue
            if inc.source == out.destination:
                return None  # money going back to a payer looks like a refund
            amount = amount_in(inc, out.currency)
            if amount is not None:
                counted.append((inc, amount))
        counted.reverse()
        payers = {inc.source for inc, _ in counted}
        total = sum((amount for _, amount in counted), Decimal(0))
        if (
            len(payers) < self.config.min_payers
            or total < threshold
            or out.amount < total * self.config.min_onward_ratio
        ):
            return None
        return self._hit(out, [inc for inc, _ in counted], len(payers), total)

    def _hit(
        self, out: TransactionFact, incoming: list[TransactionFact], payers: int, total: Decimal
    ) -> RuleHit:
        share = (out.amount / total).quantize(_CENT, rounding=ROUND_DOWN)
        elapsed = int((out.occurred_at - incoming[0].occurred_at).total_seconds())
        currency = out.currency
        explanation = (
            f"{out.source[1]} received {currency} {total:.2f} from {payers} payers in "
            f"{len(incoming)} transfers and sent {currency} {out.amount:.2f} in {out.id} "
            f"{describe_elapsed(elapsed)} after the first of them. {SIGNAL}"
        )
        return RuleHit(
            rule_id=self.rule_id,
            rule_version=self.version,
            rule_code=self.code,
            entity=out.source,
            trigger_transaction_id=out.id,
            transaction_ids=(*(inc.id for inc in incoming), out.id),
            triggered_at=out.occurred_at,
            explanation=explanation,
            metrics={
                "payer_count": str(payers),
                "incoming_count": str(len(incoming)),
                "incoming_total": f"{total:.2f}",
                "outgoing_transaction_id": out.id,
                "outgoing_amount": f"{out.amount:.2f}",
                "currency": currency,
                "onward_share": f"{share:.2f}",
                "elapsed_seconds": str(elapsed),
                "window_seconds": str(int(self.config.window.total_seconds())),
                "min_payers": str(self.config.min_payers),
                "min_onward_ratio": f"{self.config.min_onward_ratio:.2f}",
            },
        )
