"""Labelled synthetic scenario families, generated from a seed.

Labels come from the RAPID_ONWARD_TRANSFER contract text (its `description`), never from the
rule's output: completed transfers only, same currency, onward within the window (inclusive), at
least the minimum share, incoming at least the threshold, transfers back to the sender ignored.
Where the contract is silent the label rule below says what we decided (design §8).
"""

import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.modules.detection.facts import Conversion, PartyKey, TransactionFact
from app.modules.detection.rules.rapid_onward_transfer import RapidOnwardTransferConfig
from app.modules.transactions.models import TransactionStatus

CONFIG = RapidOnwardTransferConfig()
WINDOW_S = int(CONFIG.window.total_seconds())
THRESHOLD = CONFIG.min_incoming_amount["INR"]
RATIO = CONFIG.min_onward_ratio
CENT = Decimal("0.01")
EPOCH = datetime(2026, 10, 1, tzinfo=UTC)


@dataclass(frozen=True)
class Variant:
    family: str
    index: int
    facts: tuple[TransactionFact, ...]
    expect_alert: bool
    expected_pairs: frozenset[tuple[str, str]]  # (incoming, onward) the contract says must alert
    start_ids: tuple[str, ...]  # where path finding starts; empty when paths are not scored
    expected_paths: frozenset[tuple[str, ...]]  # transaction IDs, in path order


class _Builder:
    """IDs and helpers for one variant: TX-8<family><variant><n> (numeric, like real IDs, so the
    answer validator's ID check applies), parties ACC-B…/BEN-B…."""

    def __init__(self, family_no: int, index: int, rng: random.Random) -> None:
        self.tag = f"{family_no:02d}{index:04d}"
        self.rng = rng
        self.start = EPOCH + timedelta(hours=index)
        self.count = 0

    def acc(self, letter: str) -> PartyKey:
        return ("account", f"ACC-B{self.tag}{letter}")

    def ben(self, letter: str) -> PartyKey:
        return ("beneficiary", f"BEN-B{self.tag}{letter}")

    def amount(self, low: Decimal, high: Decimal) -> Decimal:
        cents = self.rng.randint(int(low * 100), int(high * 100))
        return (Decimal(cents) / 100).quantize(CENT)

    def tx(
        self,
        source: PartyKey,
        destination: PartyKey,
        amount: Decimal,
        at_s: int,
        *,
        currency: str = "INR",
        status: TransactionStatus = TransactionStatus.SETTLED,
        reversed_by: tuple[str, ...] = (),
        reverses: str | None = None,
        converted: Conversion | None = None,
    ) -> TransactionFact:
        self.count += 1
        return TransactionFact(
            id=f"TX-8{self.tag}{self.count}",
            source=source,
            destination=destination,
            amount=amount,
            currency=currency,
            occurred_at=self.start + timedelta(seconds=at_s),
            status=status,
            reversed_by=reversed_by,
            reverses=reverses,
            rail="IMPS",
            converted=converted,
        )

    def incoming(self) -> Decimal:
        return self.amount(THRESHOLD, THRESHOLD * 20)

    def onward(self, incoming: Decimal) -> Decimal:
        return self.amount((incoming * RATIO).quantize(CENT), incoming)

    def elapsed(self) -> int:
        return self.rng.randint(1, WINDOW_S)


def _variant(
    name: str,
    index: int,
    facts: Sequence[TransactionFact],
    pairs: Sequence[tuple[TransactionFact, TransactionFact]] = (),
    paths: Sequence[Sequence[TransactionFact]] = (),
) -> Variant:
    return Variant(
        family=name,
        index=index,
        facts=tuple(facts),
        expect_alert=bool(pairs),
        expected_pairs=frozenset((a.id, b.id) for a, b in pairs),
        start_ids=(facts[0].id,) if paths else (),
        expected_paths=frozenset(tuple(f.id for f in p) for p in paths),
    )


Build = Callable[[_Builder, int], Variant]


# --- positives --------------------------------------------------------------------------------


def _rapid_onward(b: _Builder, i: int) -> Variant:
    amount = THRESHOLD if i == 1 else b.incoming()  # Variant 1: exactly at the threshold.
    onward = (amount * RATIO).quantize(CENT) if i == 2 else b.onward(amount)  # 2: exactly 50 %.
    elapsed = WINDOW_S if i == 0 else b.elapsed()  # Variant 0: exactly at the window.
    inc = b.tx(b.acc("S"), b.acc("M"), amount, 0)
    out = b.tx(b.acc("M"), b.ben("D"), onward, elapsed)
    return _variant("rapid_onward", i, [inc, out], [(inc, out)], [[inc, out]])


def _chain(b: _Builder, hops: int) -> list[TransactionFact]:
    parties = [b.acc("S"), *(b.acc(f"M{n}") for n in range(1, hops)), b.ben("D")]
    amount, at = b.incoming(), 0
    facts: list[TransactionFact] = []
    for n in range(hops):
        facts.append(b.tx(parties[n], parties[n + 1], amount, at))
        amount = b.amount(max(THRESHOLD, (amount * RATIO).quantize(CENT)), amount)
        at += b.rng.randint(1, WINDOW_S // 2)
    return facts


def _two_hop(b: _Builder, i: int) -> Variant:
    facts = _chain(b, 3)
    pairs = [(facts[0], facts[1]), (facts[1], facts[2])]
    return _variant("two_hop", i, facts, pairs, [facts])


def _multi_hop(b: _Builder, i: int) -> Variant:
    facts = _chain(b, 4 if i % 5 == 4 else 3)
    pairs = list(zip(facts, facts[1:], strict=False))
    # The path finder stops at 3 hops, so a 4-hop chain is expected truncated to its first 3.
    return _variant("multi_hop", i, facts, pairs, [facts[:3]])


def _circular(b: _Builder, i: int) -> Variant:
    s, m, n = b.acc("S"), b.acc("M"), b.acc("N")
    a1 = b.incoming()
    a2 = b.amount(max(THRESHOLD, (a1 * RATIO).quantize(CENT)), a1)
    a3 = b.amount((a2 * RATIO).quantize(CENT), a2)
    t1 = b.tx(s, m, a1, 0)
    t2 = b.tx(m, n, a2, b.rng.randint(1, WINDOW_S // 2))
    t3 = b.tx(n, s, a3, int((t2.occurred_at - b.start).total_seconds()) + b.elapsed() // 2)
    return _variant("circular", i, [t1, t2, t3], [(t1, t2), (t2, t3)], [[t1, t2, t3]])


def _duplicate_incoming(b: _Builder, i: int) -> Variant:
    # Label rule: a repeated incoming record with a qualifying onward transfer still alerts;
    # the expected pair is the most recent qualifying incoming (the contract's "received").
    amount = b.incoming()
    first = b.tx(b.acc("S"), b.acc("M"), amount, 0)
    again = b.tx(b.acc("S"), b.acc("M"), amount, b.rng.randint(1, 60))
    out = b.tx(b.acc("M"), b.ben("D"), b.onward(amount), 60 + b.elapsed() // 2)
    return _variant("duplicate_incoming", i, [first, again, out], [(again, out)])


# --- negatives --------------------------------------------------------------------------------


def _pair(
    name: str,
    b: _Builder,
    i: int,
    *,
    amount: Decimal | None = None,
    onward: Decimal | None = None,
    elapsed: int | None = None,
    out_to: PartyKey | None = None,
    incoming_status: TransactionStatus = TransactionStatus.SETTLED,
    onward_currency: str = "INR",
) -> Variant:
    amount = b.incoming() if amount is None else amount
    inc = b.tx(b.acc("S"), b.acc("M"), amount, 0, status=incoming_status)
    out = b.tx(
        b.acc("M"),
        out_to or b.ben("D"),
        b.onward(amount) if onward is None else onward,
        b.elapsed() if elapsed is None else elapsed,
        currency=onward_currency,
    )
    return _variant(name, i, [inc, out])


def _converted_onward(b: _Builder, i: int) -> Variant:
    """INR in, USD out; the onward record states its INR cost and rate (variant 0: exactly 50 %)."""
    amount = b.incoming()
    inr = (amount * RATIO).quantize(CENT) if i == 0 else b.onward(amount)
    rate = b.amount(Decimal("82.00"), Decimal("84.99"))
    inc = b.tx(b.acc("S"), b.acc("M"), amount, 0)
    out = b.tx(
        b.acc("M"),
        b.ben("D"),
        (inr / rate).quantize(CENT),
        b.elapsed(),
        currency="USD",
        converted=Conversion(inr, "INR", rate),
    )
    return _variant("converted_onward", i, [inc, out], pairs=[(inc, out)])


def _onward_after_window(b: _Builder, i: int) -> Variant:
    late = WINDOW_S + (1 if i == 0 else b.rng.randint(1, 600))
    return _pair("onward_after_window", b, i, elapsed=late)


def _incoming_below_threshold(b: _Builder, i: int) -> Variant:
    amount = THRESHOLD - CENT if i == 0 else b.amount(Decimal("100.00"), THRESHOLD - CENT)
    return _pair("incoming_below_threshold", b, i, amount=amount)


def _onward_below_ratio(b: _Builder, i: int) -> Variant:
    amount = b.incoming()
    floor = (amount * RATIO).quantize(CENT)
    onward = floor - CENT if i == 0 else b.amount(Decimal("1.00"), floor - CENT)
    return _pair("onward_below_ratio", b, i, amount=amount, onward=onward)


def _return_to_sender(b: _Builder, i: int) -> Variant:
    return _pair("return_to_sender", b, i, out_to=b.acc("S"))


def _pending_incoming(b: _Builder, i: int) -> Variant:
    return _pair("pending_incoming", b, i, incoming_status=TransactionStatus.PENDING)


def _failed_incoming(b: _Builder, i: int) -> Variant:
    return _pair("failed_incoming", b, i, incoming_status=TransactionStatus.FAILED)


def _currency_mismatch(b: _Builder, i: int) -> Variant:
    return _pair("currency_mismatch", b, i, onward_currency="USD")


def _onward_before_incoming(b: _Builder, i: int) -> Variant:
    # Label rule: money sent before it arrived is not "sent onward"; negative.
    return _pair("onward_before_incoming", b, i, elapsed=-b.rng.randint(1, WINDOW_S))


def _reversed_incoming(b: _Builder, i: int) -> Variant:
    amount = b.incoming()
    reversal_id = f"TX-8{b.tag}3"
    inc = b.tx(b.acc("S"), b.acc("M"), amount, 0, reversed_by=(reversal_id,))
    out = b.tx(b.acc("M"), b.ben("D"), b.onward(amount), b.elapsed())
    back = b.tx(b.acc("M"), b.acc("S"), amount, WINDOW_S * 2, reverses=inc.id)
    return _variant("reversed_incoming", i, [inc, out, back])


def _benign_high_value(b: _Builder, i: int) -> Variant:
    big = b.amount(THRESHOLD * 50, THRESHOLD * 200)
    return _variant("benign_high_value", i, [b.tx(b.acc("S"), b.ben("D"), big, 0)])


@dataclass(frozen=True)
class Family:
    name: str
    description: str
    label_rule: str
    build: Build


FAMILIES: tuple[Family, ...] = (
    Family("rapid_onward", "Received, then sent on within the window.", "positive", _rapid_onward),
    Family("two_hop", "A → B → C → D, each hop qualifying.", "positive, 2 pairs", _two_hop),
    Family(
        "multi_hop",
        "Chains of 3 or 4 qualifying hops.",
        "positive, every qualifying pair; paths truncated at 3 hops",
        _multi_hop,
    ),
    Family("circular", "S → M → N → S.", "positive, 2 pairs; one cycle path", _circular),
    Family(
        "duplicate_incoming",
        "The same incoming transfer recorded twice, then sent on.",
        "positive; pair is the most recent incoming",
        _duplicate_incoming,
    ),
    Family(
        "onward_after_window", "Sent on 1–600 s after the window.", "negative", _onward_after_window
    ),
    Family(
        "incoming_below_threshold",
        "Incoming below INR 10,000.00.",
        "negative",
        _incoming_below_threshold,
    ),
    Family("onward_below_ratio", "Onward below 50 % of incoming.", "negative", _onward_below_ratio),
    Family("return_to_sender", "Sent back to the sender.", "negative", _return_to_sender),
    Family(
        "reversed_incoming",
        "Incoming later undone by a reversal record.",
        "negative",
        _reversed_incoming,
    ),
    Family("pending_incoming", "Incoming still pending.", "negative", _pending_incoming),
    Family("failed_incoming", "Incoming failed.", "negative", _failed_incoming),
    Family("currency_mismatch", "INR in, USD out.", "negative", _currency_mismatch),
    Family(
        "onward_before_incoming",
        "Onward timestamp earlier than the incoming one.",
        "negative",
        _onward_before_incoming,
    ),
    Family(
        "benign_high_value", "One large transfer, nothing sent on.", "negative", _benign_high_value
    ),
    # Appended, not grouped with the positives: a family's position sets its IDs.
    Family(
        "converted_onward",
        "INR in, USD out; the transfer records its INR cost and rate.",
        "positive",
        _converted_onward,
    ),
)


def generate(seed: int, variants: int) -> list[Variant]:
    """`variants` per family; each family has its own RNG so adding one never shifts the rest."""
    out: list[Variant] = []
    for family_no, family in enumerate(FAMILIES, 1):
        rng = random.Random(f"{seed}:{family.name}")  # noqa: S311  (reproducible data, not secrets)
        out += [family.build(_Builder(family_no, i, rng), i) for i in range(variants)]
    return out
