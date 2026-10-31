from datetime import datetime

from pydantic import BaseModel

from app.modules.safety.contract import Category, CheckStatus


class SafetyCheckOut(BaseModel):
    id: str
    category: Category
    attack: str
    defence: str


class SafetyResultOut(SafetyCheckOut):
    status: CheckStatus
    observed: str
    duration_ms: int


class SafetyCounts(BaseModel):
    passed: int
    failed: int
    skipped: int


class SafetyRunOut(BaseModel):
    ran_at: datetime
    duration_ms: int
    counts: SafetyCounts
    results: list[SafetyResultOut]
