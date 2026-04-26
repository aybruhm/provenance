class SentinelError(Exception):
    """Base class for all Sentinel SDK errors."""


class EscalationError(SentinelError):
    """
    Raised when an escalation is in progress and the tool call cannot proceed.
    """

    def __init__(self, action: str, escalation_id: str) -> None:
        self.action = action
        self.escalation_id = escalation_id
        super().__init__(
            f"[ESCALATE] Escalation in progress for '{action}'  (esc={escalation_id})"
        )


class PolicyBlockedError(SentinelError):
    """
    Raised when a tool call is blocked by the active policy.

    Attributes:
        action      the tool-call action that was blocked
        reason      human-readable explanation from the policy engine
        event_id    the audit event ID for this blocked call
    """

    def __init__(self, action: str, reason: str, event_id: str) -> None:
        self.action = action
        self.reason = reason
        self.event_id = event_id
        super().__init__(f"[BLOCK] {action}: {reason}  (event={event_id})")


class EscalationTimeoutError(SentinelError):
    """
    Raised when an escalation hold expires before a human decision is made.
    The tool call is implicitly blocked on timeout.
    """

    def __init__(self, action: str, escalation_id: str) -> None:
        self.action = action
        self.escalation_id = escalation_id
        super().__init__(
            f"[TIMEOUT] Escalation for '{action}' timed out  (esc={escalation_id})"
        )


class GatewayError(SentinelError):
    """
    Raised when the Sentinel gateway cannot be reached and the client
    is configured with on_gateway_error='closed'.
    """

    def __init__(self, url: str, cause: Exception) -> None:
        self.url = url
        self.cause = cause
        super().__init__(f"Sentinel gateway unreachable at {url}: {cause}")
