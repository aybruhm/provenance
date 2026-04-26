"""
Example 2: @guard decorator (sync + async)

Wrap any callable with @provenance.guard("action") to intercept it before
execution. Provenance evaluates the policy; if allowed, the function runs
normally. If blocked, PolicyBlockedError is raised before the function body
is ever entered.
"""

import asyncio

from provenance_client import ProvenanceClient, ProvenanceGateway
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


# ── sync guard ────────────────────────────────────────────────────────────────


@provenance.guard("payments.initiate")
def initiate_payment(amount: float, currency: str, recipient_id: str) -> dict:
    # Only reached if Provenance allows it
    return {"status": "initiated", "amount": amount, "currency": currency}


@provenance.guard("email.send")
def send_email(to: str, template: str) -> dict:
    return {"status": "sent", "to": to}


# ── async guard ───────────────────────────────────────────────────────────────


@provenance.guard("payments.initiate")
async def async_initiate_payment(
    amount: float, currency: str, recipient_id: str
) -> dict:
    await asyncio.sleep(0)  # simulate async work
    return {"status": "initiated", "amount": amount, "currency": currency}


# ── main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    print("--- Sync: £50 GBP (expect ALLOW) ---")
    try:
        result = initiate_payment(50, "GBP", "rec_abc123")
        print(f"Result: {result}")
    except PolicyBlockedError as e:
        print(f"Blocked: {e}")

    print("\n--- Sync: email.send (expect ALLOW) ---")
    try:
        result = send_email("customer@example.com", "invoice_ready")
        print(f"Result: {result}")
    except PolicyBlockedError as e:
        print(f"Blocked: {e}")

    print("\n--- Async: £50 GBP (expect ALLOW) ---")

    async def run_async():
        try:
            result = await async_initiate_payment(50, "GBP", "rec_abc123")
            print(f"Result: {result}")
        except PolicyBlockedError as e:
            print(f"Blocked: {e}")

    asyncio.run(run_async())


if __name__ == "__main__":
    main()
