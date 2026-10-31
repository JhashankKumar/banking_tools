"""Scores the real detection rule and path finder against the generated labels."""

from collections.abc import Callable, Iterable, Sequence
from typing import Any

from app.benchmark.families import Variant
from app.modules.detection.rules.rapid_onward_transfer import RapidOnwardTransfer
from app.modules.graph.paths import PathParams, find_money_paths

Scores = dict[str, Any]


def _rate(hits: int, total: int) -> float | None:
    """None when undefined (nothing to divide by), so it is never reported as 0 or 1."""
    return round(hits / total, 4) if total else None


def _by_family(
    variants: Sequence[Variant], score: Callable[[Sequence[Variant]], Scores]
) -> dict[str, Scores]:
    families = sorted({v.family for v in variants}, key=[v.family for v in variants].index)
    return {f: score([v for v in variants if v.family == f]) for f in families}


def _set_counts(found: Iterable[set[Any]], expected: Iterable[frozenset[Any]]) -> dict[str, int]:
    tp = fp = fn = 0
    for got, want in zip(found, expected, strict=True):
        tp += len(got & want)
        fp += len(got - want)
        fn += len(want - got)
    return {"tp": tp, "fp": fp, "fn": fn}


def _rule_block(variants: Sequence[Variant]) -> Scores:
    rule = RapidOnwardTransfer()
    found: list[set[tuple[str, str]]] = []
    counts = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    for v in variants:
        hits = rule.evaluate(v.facts)
        found.append({(h.transaction_ids[0], h.transaction_ids[-1]) for h in hits})
        key = ("t" if bool(hits) == v.expect_alert else "f") + ("p" if hits else "n")
        counts[key] += 1
    return {
        "variants": counts,
        "precision": _rate(counts["tp"], counts["tp"] + counts["fp"]),
        "recall": _rate(counts["tp"], counts["tp"] + counts["fn"]),
        "pairs": _set_counts(found, (v.expected_pairs for v in variants)),
    }


def score_rule(variants: Sequence[Variant]) -> Scores:
    """Per variant (should it alert?) and per (incoming, onward) pair, overall and per family."""
    return {"overall": _rule_block(variants), "families": _by_family(variants, _rule_block)}


def _path_block(variants: Sequence[Variant]) -> Scores:
    scored = [v for v in variants if v.start_ids]
    found: list[set[tuple[str, ...]]] = []
    truncated = 0
    for v in scored:
        result = find_money_paths(v.start_ids, v.facts, PathParams())
        found.append({tuple(e.fact.id for e in p.edges) for p in result.paths})
        truncated += result.truncated
    counts = _set_counts(found, (v.expected_paths for v in scored))
    return {
        "variants_scored": len(scored),
        "paths": counts,
        "precision": _rate(counts["tp"], counts["tp"] + counts["fp"]),
        "recall": _rate(counts["tp"], counts["tp"] + counts["fn"]),
        "truncated_results": truncated,
    }


def score_paths(variants: Sequence[Variant]) -> Scores:
    """Paths found from each variant's start against its generated paths (24 h, 3 hops)."""
    with_paths = [v for v in variants if v.start_ids]
    return {"overall": _path_block(with_paths), "families": _by_family(with_paths, _path_block)}
