"""What a safety check is: an attack, the defence expected to stop it, and how to try it."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from app.modules.safety.context import CheckContext

Category = Literal[
    "Prompt injection",
    "Customer information",
    "Access control",
    "Tool abuse",
    "Grounding",
    "Limits",
    "Audit and secrets",
]
CATEGORY_ORDER: tuple[Category, ...] = (
    "Prompt injection",
    "Customer information",
    "Access control",
    "Tool abuse",
    "Grounding",
    "Limits",
    "Audit and secrets",
)
CheckStatus = Literal["passed", "failed", "skipped"]


@dataclass(frozen=True)
class CheckOutcome:
    status: CheckStatus
    observed: str  # One plain sentence: synthetic IDs only, never secrets or internal messages.


def passed(observed: str) -> CheckOutcome:
    return CheckOutcome("passed", observed)


def failed(observed: str) -> CheckOutcome:
    return CheckOutcome("failed", observed)


def skipped(observed: str) -> CheckOutcome:
    return CheckOutcome("skipped", observed)


@dataclass(frozen=True)
class SafetyCheck:
    id: str
    category: Category
    attack: str
    defence: str
    run: "Callable[[CheckContext], CheckOutcome]"


class CasebookMissingError(Exception):
    """The check needs a seeded case that is not in the database."""


CASEBOOK_MISSING = "Needs the seeded casebook (python -m app.seed)"
