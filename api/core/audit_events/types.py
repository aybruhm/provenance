from pydantic import BaseModel


class ChainViolation(BaseModel):
    position: int
    event_id: str
    expected_prev_hash: str
    actual_prev_hash: str


class ChainValidationResult(BaseModel):
    tenant_id: str
    valid: bool
    events_checked: int
    violations: list[ChainViolation]