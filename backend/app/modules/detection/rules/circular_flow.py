"""CIRCULAR_FLOW v1: money that leaves a party and comes back to it in three hops. Review only.

v1 looks at three-hop cycles (A -> B -> C -> A) in one currency. Two-hop round trips look like
refunds and are left out; longer and mixed-currency cycles are not covered yet.
"""

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import ROUND_DOWN, Decimal

from app.modules.detection.contract import RuleHit
from app.modules.detection.facts import PartyKey, TransactionFact, is_completed
from app.modules.detection.rules.rapid_onward_transfer import describe_elapsed

_CENT = Decimal("0.01")
SIGNAL = "Signal for analyst review; not a finding of fraud."


def _default_thresholds() -> Mapping[str, Decimal]:
    return {"INR": Decimal("10000.00")}


def _key(fact: TransactionFact) -> tuple[datetime, str]:
    return (fact.occurred_at, fact.id)


@dataclass(frozen=True)
class CircularFlowConfig:
    window: timedelta = timedelta(hours=24)
    # Per-currency minimum first-hop amount. A currency with no threshold is out of scope.
    min_start_amount: Mapping[str, Decimal] = field(default_factory=_default_thresholds)
    min_return_ratio: Decimal = Decimal("0.50")


class CircularFlow:
    rule_id: str = "CIRCULAR_FLOW"
    version: str = "1"
    code: str = "CIR"
    title: str = "Circular flow"
    description: str = (
        "Money leaves a party and comes back to it through two other parties: three completed "
        "transfers A to B, B to C and C to A, in that order, all in one currency, within the "
        "configured window. The first transfer is at least the configured amount and the "
        "returning transfer at least the configured share of it. Two-hop round trips (which look "
        "like refunds), longer cycles and cycles across currencies are not covered."
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
        "Cash or treasury sweeps between one company's own accounts.",
        "A loan repaid through an intermediary.",
        "Family members pooling and returning funds.",
        "Records missing from the dataset (fees, other transfers, holds) may change the picture.",
    )

    def __init__(self, config: CircularFlowConfig | None = None) -> None:
        self.config = config or CircularFlowConfig()

    @property
    def parameters(self) -> Mapping[str, str]:
        thresholds = ",".join(
            f"{currency}:{amount:.2f}"
            for currency, amount in sorted(self.config.min_start_amount.items())
        )
        return {
            "window_seconds": str(int(self.config.window.total_seconds())),
            "min_start_amount": thresholds,
            "min_return_ratio": f"{self.config.min_return_ratio:.2f}",
            "hops": "3",
        }

    def evaluate(self, facts: Sequence[TransactionFact]) -> list[RuleHit]:
        completed = sorted((f for f in facts if is_completed(f) and f.reverses is None), key=_key)
        into: defaultdict[PartyKey, list[TransactionFact]] = defaultdict(list)
        for f in completed:
            into[f.destination].append(f)
        hits: list[RuleHit] = []
        for t3 in completed:
            found = self._latest_cycle(t3, into)
            if found is not None:
                hits.append(self._hit(*found, t3))
        return hits

    def _latest_cycle(
        self, t3: TransactionFact, into: Mapping[PartyKey, list[TransactionFact]]
    ) -> tuple[TransactionFact, TransactionFact] | None:
        a, c = t3.destination, t3.source
        if a == c:  # a self-transfer cannot close a cycle through three different parties
            return None
        best: tuple[TransactionFact, TransactionFact] | None = None
        for t2 in into.get(c, []):
            b = t2.source
            if _key(t2) >= _key(t3) or b in (a, c) or t2.currency != t3.currency:
                continue
            for t1 in into.get(b, []):
                if t1.source != a or _key(t1) >= _key(t2) or t1.currency != t3.currency:
                    continue
                if not self._qualifies(t1, t3):
                    continue
                if best is None or (_key(t1), _key(t2)) > (_key(best[0]), _key(best[1])):
                    best = (t1, t2)
        return best

    def _qualifies(self, t1: TransactionFact, t3: TransactionFact) -> bool:
        threshold = self.config.min_start_amount.get(t1.currency)
        return (
            threshold is not None
            and t3.occurred_at - t1.occurred_at <= self.config.window
            and t1.amount >= threshold
            and t3.amount >= t1.amount * self.config.min_return_ratio
        )

    def _hit(self, t1: TransactionFact, t2: TransactionFact, t3: TransactionFact) -> RuleHit:
        ratio = (t3.amount / t1.amount).quantize(_CENT, rounding=ROUND_DOWN)
        elapsed = int((t3.occurred_at - t1.occurred_at).total_seconds())
        currency = t1.currency
        explanation = (
            f"{t1.source[1]} sent {currency} {t1.amount:.2f} in {t1.id} and {currency} "
            f"{t3.amount:.2f} came back in {t3.id} {describe_elapsed(elapsed)} later, via "
            f"{t2.source[1]} and {t3.source[1]}. {SIGNAL}"
        )
        return RuleHit(
            rule_id=self.rule_id,
            rule_version=self.version,
            rule_code=self.code,
            entity=t1.source,
            trigger_transaction_id=t3.id,
            transaction_ids=(t1.id, t2.id, t3.id),
            triggered_at=t3.occurred_at,
            explanation=explanation,
            metrics={
                "hops": "3",
                "start_transaction_id": t1.id,
                "start_amount": f"{t1.amount:.2f}",
                "returned_amount": f"{t3.amount:.2f}",
                "currency": currency,
                "return_ratio": f"{ratio:.2f}",
                "elapsed_seconds": str(elapsed),
                "window_seconds": str(int(self.config.window.total_seconds())),
                "min_return_ratio": f"{self.config.min_return_ratio:.2f}",
            },
        )
