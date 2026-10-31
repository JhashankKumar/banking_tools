import re
from decimal import Decimal

from app.benchmark.families import FAMILIES, Variant, generate
from app.modules.detection.rules.rapid_onward_transfer import RapidOnwardTransferConfig

CONFIG = RapidOnwardTransferConfig()
THRESHOLD = CONFIG.min_incoming_amount["INR"]
SYNTHETIC = re.compile(r"^(TX-8\d+|(ACC|BEN)-B\d+[A-Z0-9]*)$")


def _by_family(seed: int = 7, variants: int = 6) -> dict[str, list[Variant]]:
    out: dict[str, list[Variant]] = {}
    for v in generate(seed, variants):
        out.setdefault(v.family, []).append(v)
    return out


def test_generate_is_deterministic() -> None:
    assert generate(20261101, 5) == generate(20261101, 5)


def test_different_seed_differs() -> None:
    assert generate(1, 5) != generate(2, 5)


def test_variant_count_per_family() -> None:
    by = _by_family(variants=6)

    assert set(by) == {f.name for f in FAMILIES}
    assert all(len(vs) == 6 for vs in by.values())
    assert len(FAMILIES) >= 15


def test_labels_follow_contract_not_rule() -> None:
    by = _by_family(variants=10)
    for v in by["onward_after_window"]:
        inc, out = v.facts[0], v.facts[1]
        assert out.occurred_at - inc.occurred_at > CONFIG.window
        assert not v.expect_alert
    for v in by["incoming_below_threshold"]:
        assert v.facts[0].amount < THRESHOLD and not v.expect_alert
    for v in by["onward_below_ratio"]:
        assert v.facts[1].amount < v.facts[0].amount * CONFIG.min_onward_ratio
    for v in by["rapid_onward"]:
        assert v.expect_alert and v.expected_pairs == {(v.facts[0].id, v.facts[1].id)}


def test_near_threshold_variants_exist() -> None:
    by = _by_family(variants=10)
    assert any(
        v.facts[1].occurred_at - v.facts[0].occurred_at == CONFIG.window for v in by["rapid_onward"]
    )
    assert any(
        v.facts[0].amount == THRESHOLD - Decimal("0.01") for v in by["incoming_below_threshold"]
    )


def test_ids_unique_across_variants() -> None:
    ids = [f.id for v in generate(3, 8) for f in v.facts]
    assert len(ids) == len(set(ids))


def test_only_synthetic_ids() -> None:
    for v in generate(3, 4):
        for f in v.facts:
            assert SYNTHETIC.match(f.id), f.id
            assert SYNTHETIC.match(f.source[1]) and SYNTHETIC.match(f.destination[1])


def test_multi_hop_includes_truncated_paths() -> None:
    lengths = {len(next(iter(v.expected_paths))) for v in _by_family(variants=10)["multi_hop"]}
    assert lengths == {3}
    hops = {len(v.facts) for v in _by_family(variants=10)["multi_hop"]}
    assert hops == {3, 4}
