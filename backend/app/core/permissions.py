"""Role-based access control: a fixed map from role to permissions (ADR 0001 #4)."""

from collections.abc import Mapping
from enum import StrEnum

from app.modules.users.models import Role


class Permission(StrEnum):
    CASE_READ = "case:read"
    TRANSACTION_READ = "transaction:read"
    ALERT_READ = "alert:read"
    EVIDENCE_READ = "evidence:read"
    CASE_TRANSITION = "case:transition"
    USER_MANAGE = "user:manage"
    AUDIT_READ = "audit:read"
    SAFETY_RUN = "safety:run"


_INVESTIGATE = frozenset(
    {
        Permission.CASE_READ,
        Permission.TRANSACTION_READ,
        Permission.ALERT_READ,
        Permission.EVIDENCE_READ,
    }
)

ROLE_PERMISSIONS: Mapping[Role, frozenset[Permission]] = {
    Role.ANALYST: _INVESTIGATE,
    Role.SUPERVISOR: _INVESTIGATE
    | {Permission.CASE_TRANSITION, Permission.USER_MANAGE, Permission.SAFETY_RUN},
    Role.AUDITOR: frozenset({Permission.AUDIT_READ, Permission.SAFETY_RUN}),
}


def has_permission(role: Role, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS[role]
