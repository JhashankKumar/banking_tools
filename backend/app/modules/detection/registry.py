"""Registered detection rules. Adding a rule: implement DetectionRule, add it here, document it."""

from app.modules.detection.contract import DetectionRule
from app.modules.detection.rules.circular_flow import CircularFlow
from app.modules.detection.rules.fan_in_collect import FanInCollect
from app.modules.detection.rules.fan_out_split import FanOutSplit
from app.modules.detection.rules.rapid_onward_transfer import RapidOnwardTransfer

RULES: tuple[DetectionRule, ...] = (
    RapidOnwardTransfer(),
    FanOutSplit(),
    FanInCollect(),
    CircularFlow(),
)


def get_rule(rule_id: str) -> DetectionRule | None:
    return next((rule for rule in RULES if rule.rule_id == rule_id), None)
