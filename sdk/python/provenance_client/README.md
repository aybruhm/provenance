# Provenance Python SDK

Policy-gated execution for AI agents. Every tool call is evaluated against your tenant's active policy before it runs, producing an immutable audit trail of ALLOW, BLOCK, and human-escalated decisions.

## Installation

```bash
pip install provenance-client
# or with uv
uv add provenance-client
```

**Requires Python 3.13+** · Licensed under [GNU GPL v2](https://github.com/aybruhm/provenance/blob/main/LICENSE)

---

## Authentication

The SDK authenticates via an API key scoped to a tenant policy. Generate one from the Provenance dashboard (or the API docs) and pass it at client construction.

```python
from provenance_client import ProvenanceClient, ProvenanceGateway

gateway = ProvenanceGateway(
    ProvenanceClient(
        gateway_url="http://localhost:4587",
        agent_id="<your-agent-id>",
        api_key="pk_live_...",
    )
)
```

The key is sent as `X-PROVENANCE-API-KEY` on every request. It encodes your tenant and active policy.

---

## Usage patterns

### 1. Direct execute

The most explicit pattern. Call `execute()` before performing any agent action; inspect the result before proceeding.

```python
from provenance_client import Decision, ProvenanceClient, ProvenanceGateway
from provenance_client.services import PolicyBlockedError

gateway = ProvenanceGateway(
    ProvenanceClient(
        gateway_url="http://localhost:4587",
        agent_id="<agent-id>",
        api_key="pk_live_...",
    )
)

try:
    result = gateway.execute(
        "payments.initiate",
        {"amount": 50, "currency": "GBP", "recipient_id": "rec_abc123"},
        decision=Decision.ALLOW,
    )
    print(result.decision)   # Decision.ALLOW
    print(result.reason)     # "Payment within approved parameters"
    print(result.event_id)   # immutable audit log entry ID
except PolicyBlockedError as e:
    print(e.reason)          # human-readable block reason
    print(e.event_id)        # audit event ID for the blocked call
```

### 2. `@guard` decorator

Gates any callable behind policy evaluation. Provenance intercepts the call before the function body runs. Works transparently on both sync and async functions.

```python
@gateway.guard("payments.initiate")
def initiate_payment(amount: float, currency: str, recipient_id: str) -> dict:
    # Only reached if policy allows it
    return payment_service.create(amount, currency, recipient_id)

@gateway.guard("email.send")
async def send_email(to: str, template: str) -> dict:
    # Only reached if policy allows it
    return await mailer.send(to, template)
```

Call them like normal functions:

```python
try:
    result = initiate_payment(50, "GBP", "rec_abc123")
except PolicyBlockedError as e:
    print(f"Blocked: {e.reason}")
```

The decorator captures all call-site arguments and includes them in the audit log automatically.

### 3. Session context manager

Groups a series of tool calls under a shared `session_id`. All events in the session are correlated in the audit log. On exit, the session logs a summary.

```python
with gateway.session("sess_checkout_flow") as sess:
    sess.execute(
        "payments.initiate",
        {"amount": 50, "currency": "GBP", "recipient_id": "rec_abc123"},
        decision=Decision.ALLOW,
    )
    sess.execute(
        "email.send",
        {"to": "customer@example.com", "template": "receipt"},
        decision=Decision.ALLOW,
    )

    print(sess.allowed_count)   # 2
    print(sess.blocked_count)   # 0
    print(sess.results)         # list[ExecutionResult]
```

### 4. Async variants

All three patterns have async counterparts. `async_execute` is used directly; `@guard` auto-detects async functions.

```python
result = await gateway.async_execute(
    "payments.initiate",
    {"amount": 50, "currency": "GBP", "recipient_id": "rec_abc123"},
    decision=Decision.ALLOW,
)
```

---

## Escalation

When a policy rule evaluates to `ESCALATE`, execution is held and a human reviewer is notified. The `async_execute` call blocks (up to `timeout` seconds) waiting for a human decision. The resolved decision — `ALLOW` or `BLOCK` — is returned as the final `ExecutionResult`.

```python
import asyncio

holder = {}

async def initiate_large_payment():
    holder["result"] = await gateway.async_execute(
        "payments.initiate",
        {"amount": 800, "currency": "GBP", "recipient_id": "rec_xyz789"},
        decision=Decision.ESCALATE,
    )

# The execution is held server-side; your reviewer approves via the dashboard
# or the escalation API while this coroutine is suspended.
await asyncio.gather(
    initiate_large_payment(),
    reviewer.approve(escalation_id, "Verified with CFO"),
)

r = holder["result"]
print(r.decision)        # Decision.ALLOW (after approval)
print(r.actor_human_id)  # identity of the human who approved
print(r.escalation_id)   # escalation record ID
```

If the escalation is **rejected**, `async_execute` raises `PolicyBlockedError`. Always catch it inside the coroutine when using `asyncio.gather`:

```python
async def initiate_jpy_payment():
    try:
        holder["result"] = await gateway.async_execute(
            "payments.initiate",
            {"amount": 100, "currency": "JPY", "recipient_id": "rec_jpy001"},
            decision=Decision.ESCALATE,
        )
    except PolicyBlockedError as e:
        holder["result"] = e   # store for inspection after gather

await asyncio.gather(
    initiate_jpy_payment(),
    reviewer.reject(escalation_id, "JPY not authorised"),
)

if isinstance(holder["result"], PolicyBlockedError):
    print(f"Rejected: {holder['result'].reason}")
```

---

## `ExecutionResult`

Returned by every execution path.

| Field | Type | Description |
|---|---|---|
| `decision` | `Decision` | `ALLOW`, `BLOCK`, or `ESCALATE` |
| `reason` | `str` | Human-readable explanation from the policy engine |
| `action` | `str` | The action string that was evaluated |
| `event_id` | `str` | Immutable audit log entry ID |
| `escalation_id` | `str \| None` | Set if the call was escalated |
| `actor_human_id` | `str \| None` | Identity of the human approver (if applicable) |
| `tool_result` | `Any` | Return value of the wrapped function (set by `@guard`) |

Convenience properties: `.allowed`, `.blocked`, `.escalated` → `bool`

---

## Exception reference

| Exception | Raised when |
|---|---|
| `PolicyBlockedError` | Policy evaluates to BLOCK, or an escalation is rejected |
| `EscalationTimeoutError` | Escalation hold expires with no human decision (60 s default) |
| `EscalationError` | Escalation is still in progress when queried |
| `GatewayError` | Gateway unreachable and `on_gateway_error="closed"` (default) |

All inherit from `ProvenanceError`.

```python
from provenance_client.services import (
    PolicyBlockedError,
    EscalationTimeoutError,
    GatewayError,
)

try:
    result = gateway.execute("payments.initiate", {...})
except PolicyBlockedError as e:
    # e.action, e.reason, e.event_id
except EscalationTimeoutError as e:
    # e.action, e.escalation_id
except GatewayError as e:
    # e.url, e.cause
```

---

## `ProvenanceClient` reference

```python
ProvenanceClient(
    gateway_url="http://localhost:4587",  # base URL of the Provenance gateway
    agent_id="<agent-id>",               # agent identity for audit logs
    api_key="pk_live_...",               # API key scoped to a tenant policy
    on_gateway_error="closed",           # "closed" (raise) | "open" (allow through)
    default_session=None,                # shared session_id; auto-generated if omitted
    timeout=90.0,                        # seconds — set high for escalations
)
```

### Fail-open mode

By default (`on_gateway_error="closed"`), a gateway connection failure raises `GatewayError`. Set `on_gateway_error="open"` to allow all calls through when the gateway is unreachable, with a warning:

```python
client = ProvenanceClient(
    gateway_url="http://localhost:4587",
    agent_id="<agent-id>",
    api_key="pk_live_...",
    on_gateway_error="open",
)
```

### Resource cleanup

Close the underlying HTTP client when your application shuts down:

```python
# Sync
client.close()

# Async
await client.aclose()
```

---

## Environment variables

Store credentials in the environment rather than hardcoding them:

```bash
export PROVENANCE_GATEWAY_URL="http://localhost:4587"
export PROVENANCE_AGENT_ID="<agent-id>"
export PROVENANCE_API_KEY="pk_live_..."
```

```python
import os
from provenance_client import ProvenanceClient, ProvenanceGateway

gateway = ProvenanceGateway(
    ProvenanceClient(
        gateway_url=os.environ["PROVENANCE_GATEWAY_URL"],
        agent_id=os.environ["PROVENANCE_AGENT_ID"],
        api_key=os.environ["PROVENANCE_API_KEY"],
    )
)
```
