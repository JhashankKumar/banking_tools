from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, Enum, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column


def pg_enum[E: StrEnum](enum_class: type[E], name: str) -> Enum:
    """Native PostgreSQL enum that stores the enum *values* (lowercase strings)."""

    def values(members: type[E]) -> list[str]:
        return [member.value for member in members]

    return Enum(enum_class, name=name, values_callable=values)


class SyntheticRecordMixin:
    """Columns every business record carries: synthetic marker and scenario provenance."""

    is_synthetic: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    scenario_id: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
