"""
Example 4: Async patterns (execute + escalation handling)

Demonstrates async_execute, concurrent escalation handling, and the guard
decorator on async functions. Mirrors the large-payment and JPY flows from
the e2e_demo.
"""

import asyncio

import httpx

from provenance_client import Decision, ProvenanceClient, ProvenanceGateway
from provenance_client.services import PolicyBlockedError

GATEWAY_URL = "http://localhost:4587"
TENANT_ID = "xxxxxx-xxxx-xxxx-xxxx-xxxxxx"
_API_KEY = "pk_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

provenance = ProvenanceGateway(
    ProvenanceClient(
        gateway_url=GATEWAY_URL,
        agent_id="xxxxxx-xxxx-xxxx-xxxx-xxxxxx",
        api_key=_API_KEY,
    )
)


# ── escalation helpers ────────────────────────────────────────────────────────


async def _poll_pending(token: str, delay: float = 0.4) -> str | None:
    headers = {"X-PROVENANCE-API-KEY": f"{token}"}
    async with httpx.AsyncClient(
        base_url=GATEWAY_URL,
        headers=headers,
        trust_env=False,
    ) as c:
        for _ in range(20):
            await asyncio.sleep(delay)
            resp = await c.get(
                "/v1/escalations/pending", params={"tenant_id": TENANT_ID}
            )
            resp_json = resp.json()
            pending = resp_json.get("pending", [])
            if pending:
                return pending[0]["id"]
    return None


async def auto_approve(token: str, approver: str, reason: str) -> None:
    esc_id = await _poll_pending(token)
    if not esc_id:
        print("  No pending escalation found.")
        return

    headers = {"X-PROVENANCE-API-KEY": f"{token}"}
    async with httpx.AsyncClient(
        base_url=GATEWAY_URL,
        headers=headers,
        trust_env=False,
    ) as c:
        resp = await c.post(
            f"/v1/escalations/{esc_id}/decide",
            json={"decision": "APPROVE", "approver_id": approver, "reason": reason},
        )
        resp.raise_for_status()
    print(f"  Approved by {approver}  (esc={esc_id})")


async def auto_reject(token: str, approver: str, reason: str) -> None:
    esc_id = await _poll_pending(token)
    if not esc_id:
        print("  No pending escalation found.")
        return

    headers = {"X-PROVENANCE-API-KEY": f"{token}"}
    async with httpx.AsyncClient(
        base_url=GATEWAY_URL,
        headers=headers,
        trust_env=False,
    ) as c:
        resp = await c.post(
            f"/v1/escalations/{esc_id}/decide",
            json={"decision": "REJECT", "approver_id": approver, "reason": reason},
        )
        resp.raise_for_status()
    print(f"  Rejected by {approver}  (esc={esc_id})")


# ── main ──────────────────────────────────────────────────────────────────────


async def main(token: str) -> None:
    # 1. Simple async execute — expect ALLOW
    print("--- Async execute: £50 GBP ---")
    try:
        r = await provenance.async_execute(
            "payments.initiate",
            {"amount": 50, "currency": "GBP", "recipient_id": "rec_abc123"},
            decision=Decision.ALLOW,
        )
        print(f"  {r.decision.value}: {r.reason}")
    except PolicyBlockedError as e:
        print(f"  Blocked: {e}")

    # 2. Large payment — expect ESCALATE → human APPROVES
    print("\n--- £800 GBP → ESCALATE → APPROVE ---")
    holder: dict = {}

    async def _large_payment():
        holder["r"] = await provenance.async_execute(
            "payments.initiate",
            {"amount": 800, "currency": "GBP", "recipient_id": "rec_xyz789"},
            decision=Decision.ESCALATE,
        )

    await asyncio.gather(
        _large_payment(),
        auto_approve(token, "alice@acme.com", "Verified with CFO — proceed"),
    )
    r = holder["r"]
    print(f"  {r.decision.value}: {r.reason}  (esc={r.escalation_id})")

    # 3. Disallowed currency — expect ESCALATE → REJECT
    print("\n--- JPY payment → ESCALATE → REJECT ---")

    async def _jpy_payment():
        try:
            holder["jpy"] = await provenance.async_execute(
                "payments.initiate",
                {"amount": 100, "currency": "JPY", "recipient_id": "rec_jpy001"},
                decision=Decision.ESCALATE,
            )
        except PolicyBlockedError as e:
            holder["jpy"] = e

    await asyncio.gather(
        _jpy_payment(),
        auto_reject(token, "bob@acme.com", "JPY not authorised"),
    )
    r = holder["jpy"]
    if isinstance(r, PolicyBlockedError):
        print(f"  BLOCK (rejected): {r.reason}")
    else:
        print(f"  {r.decision.value}: {r.reason}  (esc={r.escalation_id})")


if __name__ == "__main__":
    TOKEN = _API_KEY
    asyncio.run(main(TOKEN))
