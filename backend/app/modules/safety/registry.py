"""The catalogue: every check, ordered by category, then ID."""

from app.modules.safety.checks import (
    access,
    audit,
    customer_info,
    grounding,
    injection,
    limits,
    tools,
)
from app.modules.safety.contract import CATEGORY_ORDER, SafetyCheck

CATALOGUE: tuple[SafetyCheck, ...] = tuple(
    sorted(
        [
            *injection.CHECKS,
            *customer_info.CHECKS,
            *access.CHECKS,
            *tools.CHECKS,
            *grounding.CHECKS,
            *limits.CHECKS,
            *audit.CHECKS,
        ],
        key=lambda c: (CATEGORY_ORDER.index(c.category), c.id),
    )
)
