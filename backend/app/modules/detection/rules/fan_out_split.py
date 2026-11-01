"""FAN_OUT_SPLIT v1: one large credit sent on in several smaller transfers. For review only."""

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
    return {"INR": Decimal("50000.00")}


@dataclass(frozen=True)
class FanOutSplitConfig:
    window: timedelta = timedelta(minutes=30)
    # Per-currency minimum incoming amount. A currency with no threshold is out of scope.
    min_incoming_amount: Mapping[str, Decimal] = field(default_factory=_default_thresholds)
    min_transfers: int = 3
    min_onward_share: Decimal = Decimal("0.80")


class FanOutSplit:
    rule_id: str = "FAN_OUT_SPLIT"
    version: str = "1"
    code: str = "FOS"
    title: str = "Fan-out split"
    description: str = (
        "An account or beneficiary receives a completed transfer of at least the configured "
        "amount and, within the configured window, sends at least the configured number of "
        "separate completed transfers that together reach the configured share of it. Transfers "
        "back to the sender are not counted. Transfers in another currency count only through "
        "the converted amount stated on the record."
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
        "Payroll or vendor batch payments made right after funding arrives.",
        "A business distributing funds to its own accounts.",
        "Loan or grant disbursements paid on to several suppliers.",
        "Records missing from the dataset (fees, other transfers, holds) may change the picture.",
    )

    def __init__(self, config: FanOutSplitConfig | None = None) -> None:
        self.config = config or FanOutSplitConfig()

    @property
    def parameters(self) -> Mapping[str, str]:
        thresholds = ",".join(
            f"{currency}:{amount:.2f}"
            for currency, amount in sorted(self.config.min_incoming_amount.items())
        )
        return {
            "window_seconds": str(int(self.config.window.total_seconds())),
            "min_incoming_amount": thresholds,
            "min_transfers": str(self.config.min_transfers),
            "min_onward_share": f"{self.config.min_onward_share:.2f}",
        }

    def evaluate(self, facts: Sequence[TransactionFact]) -> list[RuleHit]:
        completed = sorted(
            (f for f in facts if is_completed(f) and f.reverses is None),
            key=lambda f: (f.occurred_at, f.id),
        )
        hits: list[RuleHit] = []
        used_triggers: set[str] = set()
        for index, inc in enumerate(completed):
            threshold = self.config.min_incoming_amount.get(inc.currency)
            if threshold is None or inc.amount < threshold:
                continue
            hit = self._split_after(inc, completed[index + 1 :])
            if hit is not None and hit.trigger_transaction_id not in used_triggers:
                used_triggers.add(hit.trigger_transaction_id)
                hits.append(hit)
        return hits

    def _split_after(
        self, inc: TransactionFact, later: Sequence[TransactionFact]
    ) -> RuleHit | None:
        counted: list[TransactionFact] = []
        total = Decimal(0)
        for out in later:
            if out.occurred_at - inc.occurred_at > self.config.window:
                break
            if out.source != inc.destination or out.destination == inc.source:
                continue
            amount = amount_in(out, inc.currency)
            if amount is None:
                continue
            counted.append(out)
            total += amount
            if (
                len(counted) >= self.config.min_transfers
                and total >= inc.amount * self.config.min_onward_share
            ):
                return self._hit(inc, counted, total)
        return None

    def _hit(self, inc: TransactionFact, counted: list[TransactionFact], total: Decimal) -> RuleHit:
        trigger = counted[-1]
        share = (total / inc.amount).quantize(_CENT, rounding=ROUND_DOWN)
        elapsed = int((trigger.occurred_at - inc.occurred_at).total_seconds())
        entity_id = inc.destination[1]
        explanation = (
            f"{entity_id} received {inc.currency} {inc.amount:.2f} in {inc.id} and sent "
            f"{inc.currency} {total:.2f} ({int(share * 100)}%) onward in {len(counted)} transfers "
            f"within {describe_elapsed(elapsed)}. {SIGNAL}"
        )
        return RuleHit(
            rule_id=self.rule_id,
            rule_version=self.version,
            rule_code=self.code,
            entity=inc.destination,
            trigger_transaction_id=trigger.id,
            transaction_ids=(inc.id, *(out.id for out in counted)),
            triggered_at=trigger.occurred_at,
            explanation=explanation,
            metrics={
                "incoming_transaction_id": inc.id,
                "incoming_amount": f"{inc.amount:.2f}",
                "currency": inc.currency,
                "outgoing_count": str(len(counted)),
                "outgoing_total": f"{total:.2f}",
                "onward_share": f"{share:.2f}",
                "elapsed_seconds": str(elapsed),
                "window_seconds": str(int(self.config.window.total_seconds())),
                "min_transfers": str(self.config.min_transfers),
                "min_onward_share": f"{self.config.min_onward_share:.2f}",
            },
        )
