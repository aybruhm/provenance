# [Proof-of-Concept] Provenance - Agentic Audit & Compliance Layer

Provenance is a compliance and governance middleware for AI agent deployments. It enables enterprises and AI-native companies to deploy autonomous agents with confidence by providing:

- tamper-evident audit logging of all agent actions
- real-time policy enforcement before execution
- human-in-the-loop escalation for high-risk operations
- exportable compliance reports for SOC 2, GDPR, and PCI-DSS frameworks

## Problem Statement: The Trust Deficit in Agentic AI

Enterprises are being asked to deploy AI agents that not only advise, but act autonomously.
These agents initiate payments, send communications, modify records, and provision infrastructure.
Yet the tooling ecosystem provides no standardized answer to the following questions a CISO, CTO, or compliance officer will ask before signing off on deployment:

- What actions did this agent take, and when?
- Was each action within its authorized scope?
- Who approved high-risk actions?
- Can we produce an audit trail for the regulator?
- If the agent made a mistake, can we trace the exact decision chain?

Without answers to these questions, enterprises either block AI agent deployment entirely or accept unquantified risk. Both outcomes are commercially damaging.

## How It Works

Every agent action is routed through the Provenance gateway before execution:

```
Agent  →  Provenance Gateway  →  Policy Engine  →  ALLOW / BLOCK / ESCALATE
                                                        ↓
                                               Append-only Audit Log
                                               (hash-chained, tamper-evident)
                                                        ↓
                                          ESCALATE: Human Approver (async)
```

1. The **agent** sends an action request to the Provenance gateway instead of executing directly.
2. The **policy engine** evaluates the action against a declarative per-tenant policy.
3. The gateway returns a decision: `ALLOW`, `BLOCK`, or `ESCALATE`.
4. Every decision is appended to a **hash-chained audit log** — each entry includes a hash of the previous entry, making tampering detectable.
5. `ESCALATE` decisions are held pending a **human approver**. If no decision is made within the timeout window, the action is blocked.
6. **Compliance reports** (SOC 2, GDPR, PCI-DSS) can be generated at any time from the audit log.

**Stack:** Python 3.13 · FastAPI · PostgreSQL · SQLAlchemy (async) · Alembic · Docker

## Python SDK

The `provenance-client` package is available on PyPI. Install it to integrate Provenance policy gating into your Python agents:

```bash
pip install provenance-client
# or with uv
uv add provenance-client
```

**Requires Python 3.13+** · [SDK documentation](sdk/python/provenance_client/README.md) · [Examples](sdk/python/examples/)

```python
from provenance_client import ProvenanceClient, ProvenanceGateway, Decision

gateway = ProvenanceGateway(
    ProvenanceClient(
        gateway_url="http://localhost:4587",
        agent_id="<your-agent-id>",
        api_key="pk_live_...",
    )
)

result = gateway.execute("payments.initiate", {"amount": 50, "currency": "GBP"}, decision=Decision.ALLOW)
print(result.decision)  # Decision.ALLOW
```

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager)
- Python 3.13+

## Installation

After cloning the repository, install dependencies:

```bash
uv sync
```

### Usage

#### Configure environment

Copy the template and fill in your values; the application will not start without them:

```bash
cp api/.env.template api/.env
```

| Variable        | Description                            |
| --------------- | -------------------------------------- |
| `DATABASE_URL`  | PostgreSQL connection string (asyncpg) |
| `JWT_KEY`       | Secret key for signing JWT tokens      |
| `JWT_EXP`       | Token expiry in seconds                |
| `JWT_ALGORITHM` | Signing algorithm (default: `HS256`)   |

#### Run the application & apply schema migrations

Before running the `run` make command, you must authenticate with the Docker Hardened Image repository (dhi.io).
This is required because the project uses hardened container images from dhi.io in the Dockerfile.

If you prefer not to authenticate with `dhi.io`, you can update the image references in the Dockerfile under `api/docker/dev.Dockerfile` to use alternative registries.

To authenticate:

```bash
docker login -u <username> --password-stdin
```

Enter your PAT (Personal Access Token) when prompted for a password.

```bash
make run
make run_migrations
```

The API will be available at `http://localhost:4587`. Interactive docs at `http://localhost:4587/docs`.

#### Run e2e demo

Running the below command will exercise every core flow against the local gateway:

```bash
uv run tests/manual/e2e_demo.py
```

Expected Output

> **Note on hash-chain integrity:** The demo runs three separate agent sessions. Because the audit log is scoped globally, events from session 2 interleave with session 1 in the chain — causing the integrity scan to report `COMPROMISED`. This is expected demo behaviour and demonstrates that the detection mechanism is working correctly.

```bash
────────────────────────────────────────────────────────────────
  PROVENANCE  —  Agentic Audit & Compliance Layer  (POC Demo)
────────────────────────────────────────────────────────────────
[0] Agent session running on: sess_7607d711c862

[1] Authenticated as [u:abc]

[2] Tenant ID: 019dca7d-f002-7d92-86c4-93a066a2c6f6

[3] Agent ID: 019dca7f-e9b9-78c0-a098-bb87e5c60d6c

[4] Policy ID: 019dca7f-ea12-7342-953c-4263b8748706

[5] Tenant Policy ID: 019dca7f-ea83-7221-8265-761417491a77

[6] API Key: pk_live__3CxwsHps

[7] Small payment: £50 GBP  →  expect ALLOW
    Decision : ✗ BLOCK
    Reason   : Escalation TIMEOUT — action blocked

[8] Large payment: £800 GBP  →  expect ESCALATE → human APPROVES → ALLOW
    No pending escalation found!
    Decision : ✔ ALLOW
    Reason   : Payment within approved parameters — amount ≤ £500, currency approve
    Escalation : None

[9] Payment in JPY (disallowed currency)  →  expect ESCALATE → REJECT → BLOCK
    No pending escalation found!
    Decision : ✗ BLOCK
    Reason   : Escalation TIMEOUT — action blocked
    Escalation : 019dca80-0b81-76a2-b9a2-434891b0cb53

[10] data.delete (bulk)  →  expect BLOCK (hard policy)
    Decision : ✗ BLOCK
    Reason   : Data mutations require direct human action — agents are not authorized

[11] email.send  →  expect ALLOW (default passthrough)
    Decision : ✔ ALLOW
    Reason   : Email dispatch is unrestricted for this agent

[12] Audit log (hash-chained)

EVENT ID                      ACTION                          DECISION  PREV HASH
────────────────────────────  ──────────────────────────────  ────────  ────────────────────
019dca80-2c28-7290-a743-52b5  email.send                      ALLOW     715a8e5c8128a353e9...
019dca80-2bcb-7fc3-886b-dabb  data.delete                     BLOCK     a0d6c40c09de2b7cd2...
019dca80-0ba0-7392-af9f-8a79  payments.initiate               BLOCK     d95da25aeff3f41243... 👤
019dca7f-eb60-7313-8e11-b36a  payments.initiate               ALLOW     45c0be78fb87a3fd70...
019dca7f-eb31-7a50-8688-8e66  payments.initiate               BLOCK     316fc3526e9bcadefd... 👤
019dca7e-a518-7690-b7cb-1989  email.send                      ALLOW     9ca039ed587c46912e...
019dca7e-a4bc-76c2-8068-12ff  data.delete                     BLOCK     d7ccff916cfc8d581e...
019dca7e-849f-7da3-ad9c-700a  payments.initiate               BLOCK     d24e388435419a46cb... 👤
019dca7e-644f-7aa1-8ffa-bfe4  payments.initiate               ALLOW     e07b860c8c13c14e6d...
019dca7e-6428-79c2-92b0-17c8  payments.initiate               BLOCK     96ce36d4aeee5a9ee2... 👤
019dca7e-3377-7053-b7c2-c255  email.send                      ALLOW     97354cd47dae9a71fa...
019dca7e-3315-75d3-a903-01e4  data.delete                     BLOCK     291f8ccfcb77e11f06...
019dca7e-12fe-7ea1-b77f-7e57  payments.initiate               BLOCK     07785b7f497cf20486... 👤
019dca7d-f2a7-7f01-8314-634b  payments.initiate               ALLOW     15d9c92a6e8d4acfc0...
019dca7d-f27c-7e31-93d8-e23f  payments.initiate               BLOCK     91e826c6a83999637e... 👤

[13] Hash-chain integrity scan
    Chain    : ✗ COMPROMISED
    Checked  : 15 events
    Violations: [{'position': 0, 'event_id': '019dca80-2c28-7290-a743-52b53ee59faa', 'expected_prev_hash': '91e826c6a83999637ea7c25b26cef2f3bb6c6f9d1db8c8d8ef6de9e727232ad1', 'actual_prev_hash': '715a8e5c8128a353e91f282dbbe1c585bf563351d962d8baf20e7af1ac15efcf'}, {'position': 1, 'event_id': '019dca80-2bcb-7fc3-886b-dabbecd81cd2', 'expected_prev_hash': 'a7b92d6fc926e1d99e0122470aca75a2ca04d0ecbc36aed7a9dc25e6549acd62', 'actual_prev_hash': 'a0d6c40c09de2b7cd278860c04a8b0f955ac64570f397559ff794fa058674ea2'}, {'position': 2, 'event_id': '019dca80-0ba0-7392-af9f-8a79c72f76b7', 'expected_prev_hash': '715a8e5c8128a353e91f282dbbe1c585bf563351d962d8baf20e7af1ac15efcf', 'actual_prev_hash': 'd95da25aeff3f41243b2add8427a7dabb1bf6e44f4ee3f66e2f95f846509b15a'}, {'position': 3, 'event_id': '019dca7f-eb60-7313-8e11-b36a1e201955', 'expected_prev_hash': 'a0d6c40c09de2b7cd278860c04a8b0f955ac64570f397559ff794fa058674ea2', 'actual_prev_hash': '45c0be78fb87a3fd7030df05ef28a6215be6490dc30d1fe9347de2d291db92a0'}, {'position': 4, 'event_id': '019dca7f-eb31-7a50-8688-8e66e0916086', 'expected_prev_hash': 'd95da25aeff3f41243b2add8427a7dabb1bf6e44f4ee3f66e2f95f846509b15a', 'actual_prev_hash': '316fc3526e9bcadefd73e34fc15f0d4857279bd5a62b94a5b22296a208d336fd'}, {'position': 5, 'event_id': '019dca7e-a518-7690-b7cb-1989fb1a02a2', 'expected_prev_hash': '45c0be78fb87a3fd7030df05ef28a6215be6490dc30d1fe9347de2d291db92a0', 'actual_prev_hash': '9ca039ed587c46912ead9cfdf3ea47bdf38828f56b3743a0af20e8797ae59138'}, {'position': 6, 'event_id': '019dca7e-a4bc-76c2-8068-12ffd5e090fa', 'expected_prev_hash': '316fc3526e9bcadefd73e34fc15f0d4857279bd5a62b94a5b22296a208d336fd', 'actual_prev_hash': 'd7ccff916cfc8d581e18ddc4c14d3d4af1633ca2c60bd3743fcf27fd46a79c08'}, {'position': 7, 'event_id': '019dca7e-849f-7da3-ad9c-700adff12946', 'expected_prev_hash': '9ca039ed587c46912ead9cfdf3ea47bdf38828f56b3743a0af20e8797ae59138', 'actual_prev_hash': 'd24e388435419a46cb5b1d1fafd4b672028e870cb4944a01e06a22b6921918db'}, {'position': 8, 'event_id': '019dca7e-644f-7aa1-8ffa-bfe4ac124755', 'expected_prev_hash': 'd7ccff916cfc8d581e18ddc4c14d3d4af1633ca2c60bd3743fcf27fd46a79c08', 'actual_prev_hash': 'e07b860c8c13c14e6d662e45a06b8d20b4202ff54dffa564855a4aba6b350376'}, {'position': 9, 'event_id': '019dca7e-6428-79c2-92b0-17c8e8e349d8', 'expected_prev_hash': 'd24e388435419a46cb5b1d1fafd4b672028e870cb4944a01e06a22b6921918db', 'actual_prev_hash': '96ce36d4aeee5a9ee22e6113125fa7fafb2053c578e9a5da7de5865db3ec0758'}, {'position': 10, 'event_id': '019dca7e-3377-7053-b7c2-c255cff41451', 'expected_prev_hash': 'e07b860c8c13c14e6d662e45a06b8d20b4202ff54dffa564855a4aba6b350376', 'actual_prev_hash': '97354cd47dae9a71facc24376d76ca0001e6cb8ce606ed44b567c1564a44c3e1'}, {'position': 11, 'event_id': '019dca7e-3315-75d3-a903-01e47edf2e19', 'expected_prev_hash': '96ce36d4aeee5a9ee22e6113125fa7fafb2053c578e9a5da7de5865db3ec0758', 'actual_prev_hash': '291f8ccfcb77e11f06109d6ee8d18882dbf56c73b6c8a4d3f316d893a56254aa'}, {'position': 12, 'event_id': '019dca7e-12fe-7ea1-b77f-7e570b3cc167', 'expected_prev_hash': '97354cd47dae9a71facc24376d76ca0001e6cb8ce606ed44b567c1564a44c3e1', 'actual_prev_hash': '07785b7f497cf20486d511288015941aabe7161528df9bbb195973116523c910'}, {'position': 13, 'event_id': '019dca7d-f2a7-7f01-8314-634bd2cd1f42', 'expected_prev_hash': '291f8ccfcb77e11f06109d6ee8d18882dbf56c73b6c8a4d3f316d893a56254aa', 'actual_prev_hash': '15d9c92a6e8d4acfc0157dbea00de5d136cfedb88a70f40cdf8524217f0df89f'}, {'position': 14, 'event_id': '019dca7d-f27c-7e31-93d8-e23f6432019c', 'expected_prev_hash': '07785b7f497cf20486d511288015941aabe7161528df9bbb195973116523c910', 'actual_prev_hash': '91e826c6a83999637ea7c25b26cef2f3bb6c6f9d1db8c8d8ef6de9e727232ad1'}]

[14] Compliance reports

SOC 2 Type II — CC6
    Total actions  : 15
    Allowed        : 6
    Blocked        : 9  (60.0%)
    Escalated      : 6  (40.0%)
    Human approvals: 0   rejections: 0
    Chain integrity: ❌
    All agent actions were evaluated against a versioned declarative policy prior to execution. An append-only, hash-chained audit log was maintained for every action. High-risk actions were routed to a named human approver before execution. Audit chain integrity: VIOLATIONS DETECTED

GDPR Article 30
    Data access events : 3
    Agents with access : ['019dca7e-6285-7ea3-a4dd-277a62e70807', '019dca7f-e9b9-78c0-a098-bb87e5c60d6c', '019dca7d-f082-7550-8815-12e6162d33ab']

PCI-DSS Requirement 10
    Payment actions    : 9
    Allowed            : 3
    Blocked            : 6
    Human approved     : 0
    All payment-related agent actions were intercepted, policy-evaluated, and logged prior to execution. Actions exceeding the approved threshold were held for named human approval before proceeding. No payment action bypassed the Provenance gateway.

────────────────────────────────────────────────────────────────
POC COMPLETE
────────────────────────────────────────────────────────────────
All Provenance flows exercised successfully.

Interactive API docs: http://localhost:4587/docs
```

#### Integration

The Python SDK (`provenance-client`) is available on PyPI — see the [SDK documentation](sdk/python/provenance_client/README.md) to get started. If you prefer to use the APIs directly, you can find an example agent policy template [here](https://github.com/aybruhm/provenance/blob/main/api/resources/policies/agent_policy_template.json) and the e2e code [here](https://github.com/aybruhm/provenance/blob/main/api/tests/manual/e2e_demo.py). A TypeScript SDK is planned for the next iteration.

## Next Steps

- [ ] SDK implementation
    - [x] Python - PYPI release
    - [ ] Typescript - NPM release
- [ ] UI
