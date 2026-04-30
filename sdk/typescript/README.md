# Provenance TypeScript SDK

Policy-gated execution for AI agents. Every tool call is evaluated against your tenant's active policy before it runs, producing an immutable audit trail of ALLOW, BLOCK, and human-escalated decisions.

## Installation

```bash
npm install provenance-client
# or with yarn/pnpm
yarn add provenance-client
pnpm add provenance-client
```

**Requires Node.js 18+** · Licensed under [GNU GPL v2](https://github.com/aybruhm/provenance/blob/main/LICENSE)

---

## Authentication

The SDK authenticates via an API key scoped to a tenant policy. Generate one from the Provenance dashboard (or the API docs) and pass it at client construction.

```typescript
import { ProvenanceClient, ProvenanceGateway } from "provenance-client";

const gateway = new ProvenanceGateway(
  new ProvenanceClient({
    gatewayUrl: "http://localhost:4587",
    agentId: "<your-agent-id>",
    apiKey: "pk_live_...",
  })
);
```

The key is sent as `X-PROVENANCE-API-KEY` on every request. It encodes your tenant and active policy.

---

## Usage patterns

### 1. Direct execute

The most explicit pattern. Call `asyncExecute()` before performing any agent action; inspect the result before proceeding.

```typescript
import { Decision, ProvenanceClient, ProvenanceGateway, PolicyBlockedError } from "provenance-client";

const gateway = new ProvenanceGateway(
  new ProvenanceClient({
    gatewayUrl: "http://localhost:4587",
    agentId: "<agent-id>",
    apiKey: "pk_live_...",
  })
);

try {
  const result = await gateway.asyncExecute(
    "payments.initiate",
    { amount: 50, currency: "GBP", recipientId: "rec_abc123" },
    { decision: Decision.ALLOW }
  );
  console.log(result.decision);   // Decision.ALLOW
  console.log(result.reason);     // "Payment within approved parameters"
  console.log(result.eventId);    // immutable audit log entry ID
} catch (error) {
  if (error instanceof PolicyBlockedError) {
    console.log(error.reason);          // human-readable block reason
    console.log(error.eventId);         // audit event ID for the blocked call
  }
}
```

### 2. `guard` decorator

Gates any callable behind policy evaluation. Provenance intercepts the call before the function body runs. Because policy evaluations require network requests, the decorated function will always return a `Promise`.

```typescript
const initiatePayment = gateway.guard("payments.initiate")(
  async function initiatePayment(amount: number, currency: string, recipientId: string): Promise<Record<string, any>> {
    // Only reached if policy allows it
    return paymentService.create(amount, currency, recipientId);
  }
);

const sendEmail = gateway.guard("email.send")(
  async function sendEmail(to: string, template: string): Promise<Record<string, any>> {
    // Only reached if policy allows it
    return await mailer.send(to, template);
  }
);
```

Call them like normal functions:

```typescript
try {
  const result = await initiatePayment(50, "GBP", "rec_abc123");
} catch (error) {
  if (error instanceof PolicyBlockedError) {
    console.log(`Blocked: ${error.reason}`);
  }
}
```

The decorator captures all call-site arguments and includes them in the audit log automatically.

### 3. Session context manager

Groups a series of tool calls under a shared `sessionId`. All events in the session are correlated in the audit log. On exit, the session logs a summary.

```typescript
// Using the ES 'using' syntax (requires appropriate setup) or manual disposal
const sess = gateway.session("sess_checkout_flow");

try {
  await sess.asyncExecute(
    "payments.initiate",
    { amount: 50, currency: "GBP", recipientId: "rec_abc123" },
    { decision: Decision.ALLOW }
  );
  await sess.asyncExecute(
    "email.send",
    { to: "customer@example.com", template: "receipt" },
    { decision: Decision.ALLOW }
  );

  console.log(sess.allowedCount);   // 2
  console.log(sess.blockedCount);   // 0
  console.log(sess.results);        // ExecutionResult[]
} finally {
  sess[Symbol.dispose]();
}
```

### 4. Asynchronous Execution

Unlike the Python SDK, the TypeScript SDK strictly enforces asynchronous execution due to the nature of network requests in Node.js. Synchronous execution methods (like `execute()`) will throw an error advising you to use `asyncExecute()`.

```typescript
const result = await gateway.asyncExecute(
  "payments.initiate",
  { amount: 50, currency: "GBP", recipientId: "rec_abc123" },
  { decision: Decision.ALLOW }
);
```

---

## Escalation

When a policy rule evaluates to `ESCALATE`, execution is held and a human reviewer is notified. The `asyncExecute` call blocks (up to `timeout` milliseconds) waiting for a human decision. The resolved decision — `ALLOW` or `BLOCK` — is returned as the final `ExecutionResult`.

```typescript
const holder: Record<string, any> = {};

async function initiateLargePayment() {
  holder.result = await gateway.asyncExecute(
    "payments.initiate",
    { amount: 800, currency: "GBP", recipientId: "rec_xyz789" },
    { decision: Decision.ESCALATE }
  );
}

// The execution is held server-side; your reviewer approves via the dashboard
// or the escalation API while this promise is pending.
await Promise.all([
  initiateLargePayment(),
  reviewer.approve(escalationId, "Verified with CFO")
]);

const r = holder.result;
console.log(r.decision);        // Decision.ALLOW (after approval)
console.log(r.actorHumanId);    // identity of the human who approved
console.log(r.escalationId);    // escalation record ID
```

If the escalation is **rejected**, `asyncExecute` throws `PolicyBlockedError`. Always catch it inside the async function when using `Promise.all`:

```typescript
async function initiateJpyPayment() {
  try {
    holder.result = await gateway.asyncExecute(
      "payments.initiate",
      { amount: 100, currency: "JPY", recipientId: "rec_jpy001" },
      { decision: Decision.ESCALATE }
    );
  } catch (error) {
    if (error instanceof PolicyBlockedError) {
      holder.result = error;   // store for inspection after Promise.all
    }
  }
}

await Promise.all([
  initiateJpyPayment(),
  reviewer.reject(escalationId, "JPY not authorised")
]);

if (holder.result instanceof PolicyBlockedError) {
  console.log(`Rejected: ${holder.result.reason}`);
}
```

---

## `ExecutionResult`

Returned by every execution path.

| Field | Type | Description |
|---|---|---|
| `decision` | `Decision` | `ALLOW`, `BLOCK`, or `ESCALATE` |
| `reason` | `string` | Human-readable explanation from the policy engine |
| `action` | `string` | The action string that was evaluated |
| `eventId` | `string` | Immutable audit log entry ID |
| `escalationId` | `string \| undefined` | Set if the call was escalated |
| `actorHumanId` | `string \| undefined` | Identity of the human approver (if applicable) |
| `toolResult` | `any` | Return value of the wrapped function (set by `guard`) |

Convenience getters: `.allowed`, `.blocked`, `.escalated` → `boolean`

---

## Exception reference

| Exception | Raised when |
|---|---|
| `PolicyBlockedError` | Policy evaluates to BLOCK, or an escalation is rejected |
| `EscalationTimeoutError` | Escalation hold expires with no human decision (90 s default) |
| `EscalationError` | Escalation is still in progress when queried |
| `GatewayError` | Gateway unreachable and `onGatewayError="closed"` (default) |

All inherit from `ProvenanceError`.

```typescript
import {
  PolicyBlockedError,
  EscalationTimeoutError,
  GatewayError,
} from "provenance-client";

try {
  const result = await gateway.asyncExecute("payments.initiate", {});
} catch (error) {
  if (error instanceof PolicyBlockedError) {
    // error.action, error.reason, error.eventId
  } else if (error instanceof EscalationTimeoutError) {
    // error.action, error.escalationId
  } else if (error instanceof GatewayError) {
    // error.url, error.cause
  }
}
```

---

## `ProvenanceClient` reference

```typescript
new ProvenanceClient({
  gatewayUrl: "http://localhost:4587",  // base URL of the Provenance gateway
  agentId: "<agent-id>",               // agent identity for audit logs
  apiKey: "pk_live_...",               // API key scoped to a tenant policy
  onGatewayError: "closed",            // "closed" (raise) | "open" (allow through)
  defaultSession: undefined,           // shared sessionId; auto-generated if omitted
  timeout: 90000,                      // milliseconds — set high for escalations
});
```

### Fail-open mode

By default (`onGatewayError: "closed"`), a gateway connection failure throws `GatewayError`. Set `onGatewayError: "open"` to allow all calls through when the gateway is unreachable, with a warning:

```typescript
const client = new ProvenanceClient({
  gatewayUrl: "http://localhost:4587",
  agentId: "<agent-id>",
  apiKey: "pk_live_...",
  onGatewayError: "open",
});
```

### Resource cleanup

Close the underlying HTTP client when your application shuts down:

```typescript
await client.close();
```

---

## Environment variables

Store credentials in the environment rather than hardcoding them:

```bash
export PROVENANCE_GATEWAY_URL="http://localhost:4587"
export PROVENANCE_AGENT_ID="<agent-id>"
export PROVENANCE_API_KEY="pk_live_..."
```

```typescript
import { ProvenanceClient, ProvenanceGateway } from "provenance-client";

const gateway = new ProvenanceGateway(
  new ProvenanceClient({
    gatewayUrl: process.env.PROVENANCE_GATEWAY_URL || "",
    agentId: process.env.PROVENANCE_AGENT_ID || "",
    apiKey: process.env.PROVENANCE_API_KEY,
  })
);
```