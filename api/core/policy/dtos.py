from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class NormalizedOperation(StrEnum):
    EQ = "=="
    NE = "!="
    LT = "<"
    GT = ">"
    LE = "<="
    GE = ">="
    IN = "in"
    NOT_IN = "not_in"


class ConditionDTO(BaseModel):
    name: str
    field: str
    operator: NormalizedOperation
    value: Any


class RuleDTO(BaseModel):
    action: str
    reason: str
    conditions: list[ConditionDTO] | None = None


class MatchRuleDTO(RuleDTO):
    on_match: str


class ViolationRuleDTO(RuleDTO):
    on_violation: str


class CreatePolicyDTO(BaseModel):
    name: str
    version: str
    description: str
    rules: list[MatchRuleDTO | ViolationRuleDTO]


class UpdatePolicyDTO(BaseModel):
    name: str
    version: str
    description: str
    rules: list[MatchRuleDTO | ViolationRuleDTO]


class PolicyDTO(CreatePolicyDTO):
    id: str
    created_at: str
    updated_at: str
