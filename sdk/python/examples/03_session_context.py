"""
Example 3: Session context manager

Groups a sequence of tool calls under a shared session_id. All events in the
session are correlated in the audit log. On exit, the session logs a summary.
"""

from provenance_client import Decision, ProvenanceClient, ProvenanceGateway
from provenance_client.services import PolicyBlockedError

GATEWAY_URL = "http://localhost:4587"
_API_KEY = "pk_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

provenance = ProvenanceGateway(
    ProvenanceClient(
        gateway_url=GATEWAY_URL,
        agent_id="xxxxxx-xxxx-xxxx-xxxx-xxxxxx",
        api_key=_API_KEY,
    )
)


def run_checkout_flow() -> None:
    with provenance.session("sess_checkout_flow") as sess:
        # Step 1: verify payment
        try:
            r = sess.execute(
                "payments.initiate",
                {"amount": 50, "currency": "GBP", "recipient_id": "rec_abc123"},
                decision=Decision.ALLOW,
            )
            print(f"Payment  → {r.decision.value}: {r.reason}")
        except PolicyBlockedError as e:
            print(f"Payment blocked: {e}")

        # Step 2: send confirmation email
        try:
            r = sess.execute(
                "email.send",
                {"to": "customer@example.com", "template": "order_confirmed"},
                decision=Decision.ALLOW,
            )
            print(f"Email    → {r.decision.value}: {r.reason}")
        except PolicyBlockedError as e:
            print(f"Email blocked: {e}")

        print(
            f"\nSession summary — allowed={sess.allowed_count}, blocked={sess.blocked_count}"
        )


if __name__ == "__main__":
    run_checkout_flow()
