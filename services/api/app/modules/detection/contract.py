"""The contract every detection rule implements (docs/project/DETECTION_RULES.md)."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.modules.detection.facts import PartyKey, TransactionFact


@dataclass(frozen=True)
class RuleHit:
    """One reason for analyst review. Not a finding of fraud."""

    rule_id: str
    rule_version: str
    rule_code: str
    entity: PartyKey
    trigger_transaction_id: str
    transaction_ids: tuple[str, ...]  # every record the hit rests on, in time order
    triggered_at: datetime
    explanation: str
    metrics: Mapping[str, str]


class DetectionRule(Protocol):
    rule_id: str
    version: str
    code: str  # 2-6 uppercase letters, used in alert IDs
    title: str
    description: str
    required_fields: tuple[str, ...]
    false_positive_caveats: tuple[str, ...]

    @property
    def parameters(self) -> Mapping[str, str]: ...

    def evaluate(self, facts: Sequence[TransactionFact]) -> list[RuleHit]:
        """Deterministic: same facts in any order give the same hits in the same order."""
        ...
