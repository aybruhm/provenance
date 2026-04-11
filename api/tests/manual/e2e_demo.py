import asyncio
import sys
import uuid
from enum import StrEnum
from typing import Any, Dict

import aiohttp

# --- Configuration -----------------------------------------------------------

BASE = "http://localhost:4587"
SESSION = f"sess_{uuid.uuid4().hex[:12]}"
TIMOUT = aiohttp.ClientTimeout(total=90.0)
DEFAULT_POLICY_RULES = [
    {
        "action": "data.*",
        "reason": "Data mutations require direct human action — agents are not authorized",
        "on_match": "BLOCK",
    },
    {
        "action": "payments.initiate",
        "reason": "Currency not on the approved list [GBP, USD, EUR]. Escalating to compliance team for manual review.",
        "conditions": [
            {
                "name": "cuurency_check",
                "field": "currency",
                "operator": "in",
                "value": ["GBP", "USD", "EUR"],
            }
        ],
        "on_violation": "ESCALATE",
    },
    {
        "action": "payments.initiate",
        "reason": "Payment exceeds the £500 autonomous limit. Human approval required before execution.",
        "conditions": [
            {
                "name": "amount_check",
                "field": "amount",
                "operator": ">=",
                "value": 500,
            }
        ],
        "on_violation": "ESCALATE",
    },
    {
        "action": "payments.initiate",
        "reason": "Payment within approved parameters — amount ≤ £500, currency approve",
        "on_match": "ALLOW",
    },
    {
        "action": "email.send",
        "reason": "Email dispatch is unrestricted for this agent",
        "on_match": "ALLOW",
    },
    {
        "action": "*",
        "reason": "No specific policy rule matched; default block",
        "on_match": "BLOCK",
    },
]


class Decision(StrEnum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE"


# ── formatting helpers ────────────────────────────────────────────────────────

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BLUE = "\033[94m"
DIM = "\033[2m"


def header(text: str) -> None:
    width = 64
    print(f"\n{BOLD}{BLUE}{'─' * width}{RESET}")
    print(f"{BOLD}{BLUE}  {text}{RESET}")
    print(f"{BOLD}{BLUE}{'─' * width}{RESET}")


def step(n: int, label: str) -> None:
    print(f"\n{BOLD}[{n}]{RESET} {label}")


def result(decision: str, reason: str, extra: str = "") -> None:
    if decision == "ALLOW":
        badge = f"{GREEN}✔ ALLOW{RESET}"
    elif decision == "BLOCK":
        badge = f"{RED}❌ BLOCK{RESET}"
    else:
        badge = f"{YELLOW}⚠️  {decision}{RESET}"
    print(f"    Decision : {badge}")
    print(f"    Reason   : {DIM}{reason}{RESET}")
    if extra:
        print(f"    {extra}")


def section(title: str) -> None:
    print(f"\n  {CYAN}{BOLD}{title}{RESET}")


# --- get_or_create user with jwt token ---------------------------------------


async def get_or_create_user(
    client: aiohttp.ClientSession,
    username: str,
    password: str,
) -> str:
    resp = await client.post(
        f"{BASE}/v1/auth/register",
        json=dict(
            username=username,
            password=password,
        ),
    )
    server_message = await resp.json()
    if (
        resp.status != 200
        and server_message.get("detail", {}).get("message", "")
        == "Account already registered"
    ):
        resp = await client.post(
            f"{BASE}/v1/auth/login",
            json=dict(
                username=username,
                password=password,
            ),
        )
        resp.raise_for_status()

    resp_json = await resp.json()
    return resp_json["credentials"]["access_token"]  # type: ignore[return-value]


# --- get_or_create tenant ---------------------------------------


async def get_or_create_tenant(
    client: aiohttp.ClientSession,
    name: str,
    policy_id: str,
) -> str:
    res = await client.get(f"{BASE}/v1/tenants/")
    resp_json = await res.json()
    tenants = resp_json["tenants"]  # type: ignore[return-value]
    if len(tenants) >= 1:
        for tenant in tenants:
            if tenant["name"] == name:
                return tenant["id"]

    resp = await client.post(
        f"{BASE}/v1/tenants/",
        json=dict(
            name=name,
            policy_id=policy_id,
        ),
    )
    resp.raise_for_status()
    resp_json = await resp.json()
    return resp_json["tenant"]["id"]  # type: ignore[return-value]


# --- get_or_create agent ---------------------------------------


async def get_or_create_agent(
    client: aiohttp.ClientSession,
    tenant_id: str,
    name: str,
) -> str:
    res = await client.get(f"{BASE}/v1/agents/")
    resp_json = await res.json()
    agents = resp_json["agents"]  # type: ignore[return-value]
    if len(agents) >= 1:
        for agent in agents:
            if agent["name"] == name:
                return agent["id"]

    resp = await client.post(
        f"{BASE}/v1/agents/",
        json=dict(
            tenant_id=tenant_id,
            name=name,
        ),
    )
    resp.raise_for_status()
    resp_json = await resp.json()
    return resp_json["agent"]["id"]  # type: ignore[return-value]


# --- get_or_create policy ---------------------------------------


async def get_or_create_policy(
    client: aiohttp.ClientSession,
    tenant_id: str,
    name: str,
    description: str,
    rules: list[Dict[str, Any]],
    version: str = "0.1",
) -> str:
    res = await client.get(f"{BASE}/v1/policies/?tenant_id={tenant_id}")
    resp_json = await res.json()
    policies = resp_json["policies"]  # type: ignore[return-value]
    if len(policies) >= 1:
        for policy in policies:
            if policy["name"] == name:
                return policy["id"]

    resp = await client.post(
        f"{BASE}/v1/policies/",
        json=dict(
            name=name,
            version=version,
            description=description,
            rules=rules,
        ),
    )
    resp.raise_for_status()
    resp_json = await resp.json()
    return resp_json["policy"]["id"]  # type: ignore[return-value]


# --- get_or_assign tenant policy ---------------------------------------


async def get_or_assign_tenant_policy(
    client: aiohttp.ClientSession,
    tenant_id: str,
    policy_id: str,
) -> str:
    res = await client.get(f"{BASE}/v1/policies/{policy_id}?tenant_id={tenant_id}")
    resp_json = await res.json()
    if "detail" in resp_json and "message" in resp_json["detail"]:
        resp = await client.post(
            f"{BASE}/v1/policies/{policy_id}/assign",
            json=dict(tenant_id=tenant_id),
        )
        resp.raise_for_status()
        resp_json = await resp.json()
        return resp_json["tenant_policy_id"]

    tenant_policy = resp_json["policy"]  # type: ignore[return-value]
    return tenant_policy["tenant_policy_id"]


# ── gateway execute ────────────────────────────────────────────────────────────


async def execute(
    client: aiohttp.ClientSession,
    agent_id: str,
    tenant_id: str,
    tenant_policy_id: str,
    action: str,
    decision: str,
    parameters: Dict[str, Any],
) -> dict:
    resp = await client.post(
        f"{BASE}/v1/gateway/execute",
        json=dict(
            session_id=SESSION,
            agent_id=agent_id,
            tenant_id=tenant_id,
            tenant_policy_id=tenant_policy_id,
            action=action,
            decision=decision,
            parameters=parameters,
        ),
        timeout=TIMOUT,
    )
    resp.raise_for_status()
    resp_json = await resp.json()
    return resp_json  # type: ignore[return-value]


# ── escalation ────────────────────────────────────────────────────────


async def _poll_pending(
    client: aiohttp.ClientSession,
    tenant_id: str,
    delay: float = 0.4,
) -> str | None:
    """Poll until a pending escalation appears; return its ID."""
    for _ in range(20):
        await asyncio.sleep(delay)
        resp = await client.get(
            f"{BASE}/v1/escalations/pending",
            params={"tenant_id": tenant_id},
        )
        resp_json = await resp.json()
        pending = resp_json.get("pending", [])
        if pending:
            return pending[0]["id"]  # type: ignore[return-value]
    return None


async def auto_approve(
    client: aiohttp.ClientSession,
    tenant_id: str,
    approver: str,
    reason: str,
) -> str | None:
    escalation_id = await _poll_pending(client, tenant_id)
    if not escalation_id:
        print(f"    {RED}No pending escalation found!{RESET}")
        return None

    resp = await client.post(
        f"{BASE}/v1/escalations/{escalation_id}/decide",
        json=dict(
            decision="APPROVE",
            approver_id=approver,
            reason=reason,
        ),
    )
    resp.raise_for_status()
    print(
        f"    {GREEN}✔ Approved{RESET} by {BOLD}{approver}{RESET}  (esc_id={DIM}{escalation_id}{RESET})"
    )
    return escalation_id


async def auto_reject(
    client: aiohttp.ClientSession,
    tenant_id: str,
    approver: str,
    reason: str,
) -> str | None:
    escalation_id = await _poll_pending(client, tenant_id)
    if not escalation_id:
        print(f"    {RED}No pending escalation found!{RESET}")
        return None

    resp = await client.post(
        f"{BASE}/v1/escalations/{escalation_id}/decide",
        json=dict(
            decision="REJECT",
            approver_id=approver,
            reason=reason,
        ),
    )
    resp.raise_for_status()
    print(
        f"    {RED}✘ Rejected{RESET} by {BOLD}{approver}{RESET}  (esc_id={DIM}{escalation_id}{RESET})"
    )
    return escalation_id


# ── main demo ─────────────────────────────────────────────────────────────────


async def main() -> None:
    # Quick liveness check
    try:
        async with aiohttp.ClientSession() as ping:
            await ping.get(f"{BASE}/health", timeout=TIMOUT)
    except Exception:
        print(f"{RED}Sentinel gateway not reachable at {BASE}{RESET}")
        print("Start it first:  uvicorn main:app --reload --port 8000")
        sys.exit(1)

    header("SENTINEL  —  Agentic Audit & Compliance Layer  (POC Demo)")
    step(0, f"Agent session running on: {DIM}{SESSION}{RESET}")

    # Auth flow
    token = None
    async with aiohttp.ClientSession(timeout=TIMOUT) as client:
        # --- 1. Get or Create user
        token = await get_or_create_user(
            client,
            "abc",
            "qwerty",
        )
        step(1, "Authenticated as [u:abc]")

    # Prep flow
    tenant_id = None
    agent_id = None
    headers = {"Cookie": f"access_token={token}"}
    async with aiohttp.ClientSession(
        timeout=TIMOUT,
        headers=headers,
    ) as client:
        # --- 2. Get or create tenant
        tenant_id = await get_or_create_tenant(
            client,
            "acme",
            policy_id="policy_agent",
        )
        step(2, f"Tenant ID: {tenant_id}")

        # --- 3. Get or create agent
        agent_id = await get_or_create_agent(
            client,
            tenant_id,
            f"payment_agent_{uuid.uuid4().hex[:8]}",
        )
        step(3, f"Agent ID: {agent_id}")

        # --- 4. Get or create policy
        policy_name = f"policy_{uuid.uuid4().hex[:8]}"
        policy_id = await get_or_create_policy(
            client,
            tenant_id,
            name=policy_name,
            description=f"Description for policy {policy_name}",
            rules=DEFAULT_POLICY_RULES,
        )
        step(4, f"Policy ID: {policy_id}")

        # --- 5. Get or assign tenant policy
        tenant_policy_id = await get_or_assign_tenant_policy(
            client,
            tenant_id,
            policy_id,
        )
        step(5, f"Tenant Policy ID: {tenant_policy_id}")

    # Main flow
    async with aiohttp.ClientSession(
        timeout=TIMOUT,
        headers=headers,
    ) as client:
        # ── 6. Small payment → ALLOW ──────────────────────────────────────────
        step(6, "Small payment: £50 GBP  →  expect ALLOW")
        r = await execute(
            client,
            agent_id,
            tenant_id,
            tenant_policy_id,
            "payments.initiate",
            Decision.ALLOW,
            {"amount": 50, "currency": "GBP", "recipient_id": "rec_abc123"},
        )
        result(r["decision"], r["reason"])

        # ── 7. Large payment → ESCALATE → APPROVE ────────────────────────────
        step(7, "Large payment: £800 GBP  →  expect ESCALATE → human APPROVES → ALLOW")
        holder: dict = {}

        async def _do_large_payment():
            holder["large"] = await execute(
                client,
                agent_id,
                tenant_id,
                tenant_policy_id,
                "payments.initiate",
                Decision.ESCALATE,
                {"amount": 800, "currency": "GBP", "recipient_id": "rec_xyz789"},
            )

        await asyncio.gather(
            _do_large_payment(),
            auto_approve(
                client, tenant_id, "alice@acme.com", "Verified with CFO — proceed"
            ),
        )
        r = holder["large"]
        result(
            r["decision"],
            r["reason"],
            extra=f"Escalation : {DIM}{r.get('escalation_id')}{RESET}",
        )

        # ── 8. Disallowed currency → ESCALATE → REJECT ────────────────────────
        step(
            8,
            "Payment in JPY (disallowed currency)  →  expect ESCALATE → REJECT → BLOCK",
        )

        async def _do_jpy_payment():
            holder["jpy"] = await execute(
                client,
                agent_id,
                tenant_id,
                tenant_policy_id,
                "payments.initiate",
                Decision.ESCALATE,
                {"amount": 100, "currency": "JPY", "recipient_id": "rec_jpy001"},
            )

        await asyncio.gather(
            _do_jpy_payment(),
            auto_reject(
                client,
                tenant_id,
                "bob@acme.com",
                "JPY not authorised — non-standard market",
            ),
        )
        r = holder["jpy"]
        result(
            r["decision"],
            r["reason"],
            extra=f"Escalation : {DIM}{r.get('escalation_id')}{RESET}",
        )

        # ── 10. Hard-blocked action ────────────────────────────────────────────
        step(10, "data.delete (bulk)  →  expect BLOCK (hard policy)")
        r = await execute(
            client,
            agent_id,
            tenant_id,
            tenant_policy_id,
            "data.delete",
            Decision.BLOCK,
            {"table": "users", "condition": "WHERE created_at < '2020-01-01'"},
        )
        result(r["decision"], r["reason"])

        # ── 11. Default passthrough ────────────────────────────────────────────
        step(11, "email.send  →  expect ALLOW (default passthrough)")
        r = await execute(
            client,
            agent_id,
            tenant_id,
            tenant_policy_id,
            "email.send",
            Decision.ALLOW,
            {"to": "customer@example.com", "template": "invoice_ready"},
        )
        result(r["decision"], r["reason"])

        # ── 12. Audit log ──────────────────────────────────────────────────────
        step(12, "Audit log (hash-chained)")
        resp = await client.get(f"{BASE}/v1/audit/{tenant_id}")
        resp_json = await resp.json()
        events = resp_json["events"] or []  # type: ignore[assignment]
        print(
            f"\n  {'EVENT ID':28s}  {'ACTION':30s}  {'DECISION':8s}  {'PREV HASH':20s}"
        )
        print(f"  {'─' * 28}  {'─' * 30}  {'─' * 8}  {'─' * 20}")
        for event in events:
            dec_color = (
                GREEN
                if event["decision"] == "ALLOW"
                else (RED if event["decision"] == "BLOCK" else YELLOW)
            )
            esc_marker = " 👤" if event.get("escalation_id") else ""
            print(
                f"  {DIM}{event['id'][:28]}{RESET}"
                f"  {event['action'][:30]:30s}"
                f"  {dec_color}{event['decision']:8s}{RESET}"
                f"  {DIM}{event['prev_hash'][:18]}...{RESET}"
                f"{esc_marker}"
            )

        # ── 13. Integrity scan ─────────────────────────────────────────────────
        step(13, "Hash-chain integrity scan")
        resp = await client.get(f"{BASE}/v1/audit/integrity/{tenant_id}")
        resp_json = await resp.json()
        scan = resp_json["integrity"]  # type: ignore[assignment]
        status_str = (
            f"{GREEN}✔ VALID{RESET}" if scan["valid"] else f"{RED}✗ COMPROMISED{RESET}"
        )
        print(f"    Chain    : {status_str}")
        print(f"    Checked  : {scan['events_checked']} events")
        print(f"    Violations: {scan['violations'] or 'none'}")

        # ── 14. Compliance reports ─────────────────────────────────────────────
        step(14, "Compliance reports")

        section("SOC 2 Type II — CC6")
        resp = await client.get(f"{BASE}/v1/reports/{tenant_id}/soc2")
        resp_json = await resp.json()
        soc2 = resp_json["report"]  # type: ignore[assignment]
        s = soc2["summary"]
        print(f"    Total actions  : {s['total_agent_actions']}")
        print(f"    Allowed        : {GREEN}{s['allowed']}{RESET}")
        print(
            f"    Blocked        : {RED}{s['blocked']}{RESET}  ({s['block_rate_pct']}%)"
        )
        print(
            f"    Escalated      : {YELLOW}{s['escalated']}{RESET}  ({s['escalation_rate_pct']}%)"
        )
        print(
            f"    Human approvals: {s['human_approvals']}   rejections: {s['human_rejections']}"
        )
        print(
            f"    Chain integrity: {'✔' if soc2['audit_chain_integrity']['valid'] else '❌'}"
        )
        print(f"    {DIM}{soc2['attestation']}{RESET}")

        section("GDPR Article 30")
        resp = await client.get(f"{BASE}/v1/reports/{tenant_id}/gdpr")
        resp_json = await resp.json()
        gdpr = resp_json["report"]  # type: ignore[assignment]
        print(f"    Data access events : {gdpr['summary']['total_data_access_events']}")
        print(
            f"    Agents with access : {gdpr['summary']['agents_with_data_access'] or 'none'}"
        )

        section("PCI-DSS Requirement 10")
        resp = await client.get(f"{BASE}/v1/reports/{tenant_id}/pci")
        resp_json = await resp.json()
        pci = resp_json["report"]  # type: ignore[assignment]
        ps = pci["summary"]
        print(f"    Payment actions    : {ps['total_payment_actions']}")
        print(f"    Allowed            : {GREEN}{ps['allowed']}{RESET}")
        print(f"    Blocked            : {RED}{ps['blocked']}{RESET}")
        print(f"    Human approved     : {ps['human_approved']}")
        print(f"    {DIM}{pci['attestation']}{RESET}")

    header("POC COMPLETE")
    print(f"  {GREEN}All Sentinel flows exercised successfully.{RESET}\n")
    print(f"  Interactive API docs: {CYAN}http://localhost:4587/docs{RESET}\n")


if __name__ == "__main__":
    asyncio.run(main())
