from datetime import UTC, datetime
from decimal import Decimal

from app.modules.detection.facts import Conversion, PartyKey, amount_in
from tests.unit.detection.factories import fact

A: PartyKey = ("account", "ACC-1")
B: PartyKey = ("beneficiary", "BEN-1")
T0 = datetime(2026, 9, 15, 4, 0, tzinfo=UTC)


def test_amount_in_same_currency() -> None:
    assert amount_in(fact("TX-1", A, B, "100.00", T0), "INR") == Decimal("100.00")


def test_amount_in_recorded_conversion() -> None:
    converted = Conversion(Decimal("83450.00"), "INR", Decimal("83.45"))
    f = fact("TX-1", A, B, "1000.00", T0, currency="USD", converted=converted)
    assert amount_in(f, "INR") == Decimal("83450.00")


def test_amount_in_no_conversion_is_none() -> None:
    assert amount_in(fact("TX-1", A, B, "1000.00", T0, currency="USD"), "INR") is None


def test_amount_in_conversion_to_other_currency_is_none() -> None:
    converted = Conversion(Decimal("920.00"), "EUR", Decimal("0.92"))
    f = fact("TX-1", A, B, "1000.00", T0, currency="USD", converted=converted)
    assert amount_in(f, "INR") is None
