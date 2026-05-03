"""
Example 5: Human escalation

Two policy rules trigger escalation for `payments.initiate`:

  1. amount_check   — amount >= 500 → ESCALATE
  2. currency_check — currency not in [GBP, USD, EUR] → ESCALATE

When either condition is violated the gateway raises EscalationError instead
of running the action.  The agent must pause, surface the escalation ID to a
human reviewer, and only proceed once approved via the dashboard or API.

Reviewing escalations:
  1. Log in to the Provenance dashboard to view and action pending escalations.
  2. Create a new account or use your existing credentials to setup your workspace (or access an existing one if you already have it).
  3. Upon logging in, you'll be navigated to the "Escalations" tab to see any pending reviews. You can approve or reject escalations directly from the dashboard, and the agent will receive the outcome to proceed accordingly.
"""

from provenance_client import Decision, ProvenanceClient, ProvenanceGateway
from provenance_client.services import (
    EscalationError,
    EscalationTimeoutError,
    PolicyBlockedError,
)

GATEWAY_URL = "http://localhost:4587"
_API_KEY = "pk_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

provenance = ProvenanceGateway(
    ProvenanceClient(
        gateway_url=GATEWAY_URL,
        agent_id="xxxxxx-xxxx-xxxx-xxxx-xxxxxx",
        api_key=_API_KEY,
    )
)


def initiate_payment(amount: float, currency: str, recipient_id: str) -> dict:
    try:
        result = provenance.execute(
            "payments.initiate",
            {
                "amount": amount,
                "currency": currency,
                "recipient_id": recipient_id,
            },
            decision=Decision.ESCALATE,
        )
        print(f"Decision : {result.decision.value}")
        print(f"Reason   : {result.reason}")
        return {"status": "ok", "event_id": result.event_id}

    except EscalationError as e:
        # Gateway has flagged this action for human review before it can proceed.
        # Store the escalation_id and wait — do NOT execute the payment.
        print(f"Escalated: action='{e.action}'  escalation_id={e.escalation_id}")
        print("  → Payment paused. Awaiting human approval in the dashboard.")
        return {"status": "pending", "escalation_id": e.escalation_id}

    except EscalationTimeoutError as e:
        # No reviewer responded within the hold window — treat as blocked.
        print(
            f"Timeout  : escalation for '{e.action}' expired  (esc={e.escalation_id})"
        )
        print("  → Payment cancelled due to review timeout.")
        return {"status": "cancelled", "escalation_id": e.escalation_id}

    except PolicyBlockedError as e:
        print(f"Blocked  : {e.reason}  (event={e.event_id})")
        return {"status": "blocked", "event_id": e.event_id}


if __name__ == "__main__":
    # Triggers amount_check: amount >= 500 → ESCALATE
    print("--- £800 GBP (amount exceeds autonomous limit) ---")
    initiate_payment(800, "GBP", "rec_xyz789")

    print()

    # Triggers currency_check: JPY not in approved list → ESCALATE
    print("--- ¥10000 JPY (currency not on approved list) ---")
    initiate_payment(10_000, "JPY", "rec_jpy001")

    print()

    # Both rules satisfied: amount < 500, currency approved → ALLOW
    print("--- £50 GBP (within policy — expect ALLOW) ---")
    initiate_payment(50, "GBP", "rec_abc123")
