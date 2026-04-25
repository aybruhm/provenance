"""
Example 1: Direct execute (sync)

The most explicit pattern: call provenance.execute() before running any
agent action. The gateway evaluates the active policy and returns a decision.
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


def initiate_payment(amount: float, currency: str, recipient_id: str) -> dict:
    try:
        result = provenance.execute(
            "payments.initiate",
            {
                "amount": amount,
                "currency": currency,
                "recipient_id": recipient_id,
            },
            decision=Decision.ALLOW,
        )
    except PolicyBlockedError as e:
        print(f"Blocked: {e.reason}  (event={e.event_id})")
        return {}

    print(f"Decision : {result.decision.value}")
    print(f"Reason   : {result.reason}")
    return {"status": "ok", "event_id": result.event_id}


def drop_users() -> dict:
    try:
        result = provenance.execute(
            "data.delete",
            {"table": "users", "condition": "WHERE created_at < '2020-01-01'"},
            decision=Decision.BLOCK,
        )
    except PolicyBlockedError as e:
        print(f"Blocked: {e.reason}  (event={e.event_id})")
        return {}

    print(f"Decision : {result.decision.value}")
    print(f"Reason   : {result.reason}")
    return {"status": "ok", "event_id": result.event_id}


if __name__ == "__main__":
    # Small payment — expect ALLOW
    print("--- £50 GBP ---")
    initiate_payment(50, "GBP", "rec_abc123")

    # Hard-blocked action
    print("\n--- data.delete ---")
    drop_users()
