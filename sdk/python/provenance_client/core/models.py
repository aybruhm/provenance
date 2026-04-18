from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class Decision(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE"


@dataclass
class ExecutionResult:
    """
    Returned by every Provenance execution path.

    decision       ALLOW, BLOCK or ESCALATE (escalations are resolved before this is returned)
    reason         explanation from the policy engine or escalation handler
    action         the action string that was evaluated
    event_id       ID of the immutable audit log entry
    escalation_id  set if this call was escalated to a human approver
    actor_human_id identity of the human who approved (if applicable)
    tool_result    return value of the actual wrapped function (set by @guard)
    """

    decision: Decision
    reason: str
    action: str
    event_id: str
    escalation_id: Optional[str] = None
    actor_human_id: Optional[str] = None
    tool_result: Any = field(default=None, repr=False)

    @property
    def allowed(self) -> bool:
        return self.decision == Decision.ALLOW

    @property
    def blocked(self) -> bool:
        return self.decision == Decision.BLOCK

    @property
    def escalated(self) -> bool:
        return self.decision == Decision.ESCALATE
