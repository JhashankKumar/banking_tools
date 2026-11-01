import re

from app.modules.detection.registry import RULES, get_rule


def test_rule_ids_and_codes_unique() -> None:
    assert len({r.rule_id for r in RULES}) == len(RULES)
    assert len({r.code for r in RULES}) == len(RULES)


def test_rule_codes_fit_evidence_id_format() -> None:
    assert all(re.fullmatch(r"[A-Z]{2,6}", r.code) for r in RULES)


def test_every_rule_documents_caveats_and_required_fields() -> None:
    for rule in RULES:
        assert rule.title and rule.description
        assert rule.required_fields
        assert rule.false_positive_caveats
        assert rule.parameters


def test_get_rule_known_and_unknown() -> None:
    assert get_rule("RAPID_ONWARD_TRANSFER") is RULES[0]
    assert get_rule("NOPE") is None


def test_registered_rules_in_order() -> None:
    assert [r.rule_id for r in RULES] == [
        "RAPID_ONWARD_TRANSFER",
        "FAN_OUT_SPLIT",
        "FAN_IN_COLLECT",
        "CIRCULAR_FLOW",
    ]
