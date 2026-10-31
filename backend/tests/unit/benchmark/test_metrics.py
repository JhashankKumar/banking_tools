from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.benchmark.families import Variant
from app.benchmark.metrics import score_paths, score_rule
from app.modules.detection.facts import TransactionFact
from app.modules.transactions.models import TransactionStatus

T0 = datetime(2026, 10, 1, tzinfo=UTC)


def _tx(i: str, src: str, dst: str, amount: str, s: int) -> TransactionFact:
    return TransactionFact(
        id=f"TX-T{i}",
        source=("account", src),
        destination=("account", dst),
        amount=Decimal(amount),
        currency="INR",
        occurred_at=T0 + timedelta(seconds=s),
        status=TransactionStatus.SETTLED,
    )


def _v(
    family: str, facts: list[TransactionFact], pairs: set[tuple[str, str]], **kw: object
) -> Variant:
    return Variant(
        family=family,
        index=0,
        facts=tuple(facts),
        expect_alert=bool(pairs),
        expected_pairs=frozenset(pairs),
        start_ids=kw.get("start_ids", ()),  # type: ignore[arg-type]
        expected_paths=frozenset(kw.get("paths", ())),  # type: ignore[arg-type]
    )


HIT = [_tx("1", "A", "B", "20000.00", 0), _tx("2", "B", "C", "15000.00", 60)]
QUIET = [_tx("3", "D", "E", "20000.00", 0), _tx("4", "E", "F", "15000.00", 60)]


def test_rule_scores_count_variants_and_pairs() -> None:
    variants = [
        _v("pos", HIT, {("TX-T1", "TX-T2")}),  # TP
        _v("neg", QUIET, set()),  # rule alerts: FP
        _v("neg", [_tx("5", "G", "H", "50.00", 0)], set()),  # TN
        _v("pos", [_tx("6", "J", "K", "50.00", 0)], {("TX-T6", "TX-T7")}),  # FN
    ]

    s = score_rule(variants)

    assert s["overall"]["variants"] == {"tp": 1, "fp": 1, "fn": 1, "tn": 1}
    assert (s["overall"]["precision"], s["overall"]["recall"]) == (0.5, 0.5)
    assert s["overall"]["pairs"] == {"tp": 1, "fp": 1, "fn": 1}
    assert s["families"]["neg"]["variants"]["fp"] == 1
    assert s["families"]["neg"]["recall"] is None  # no positives in the family


def test_path_scores() -> None:
    found = _v("p", HIT, {("TX-T1", "TX-T2")}, start_ids=("TX-T1",), paths={("TX-T1", "TX-T2")})
    missed = _v("p", HIT, set(), start_ids=("TX-T1",), paths={("TX-T1", "TX-T9")})

    s = score_paths([found, missed])

    assert s["overall"]["paths"] == {"tp": 1, "fp": 1, "fn": 1}
    assert s["overall"]["recall"] == 0.5
    assert s["overall"]["variants_scored"] == 2
