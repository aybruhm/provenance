# [Proof-of-Concept] Sentinel - Agentic Audit & Compliance Layer

Sentinel is a compliance and governance middleware for AI agent deployments. It enables enterprises and AI-native companies to deploy autonomous agents with confidence by providing:

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

Every agent action is routed through the Sentinel gateway before execution:

```
Agent  →  Sentinel Gateway  →  Policy Engine  →  ALLOW / BLOCK / ESCALATE
                                                        ↓
                                               Append-only Audit Log
                                               (hash-chained, tamper-evident)
                                                        ↓
                                          ESCALATE: Human Approver (async)
```

1. The **agent** sends an action request to the Sentinel gateway instead of executing directly.
2. The **policy engine** evaluates the action against a declarative per-tenant policy.
3. The gateway returns a decision: `ALLOW`, `BLOCK`, or `ESCALATE`.
4. Every decision is appended to a **hash-chained audit log** — each entry includes a hash of the previous entry, making tampering detectable.
5. `ESCALATE` decisions are held pending a **human approver**. If no decision is made within the timeout window, the action is blocked.
6. **Compliance reports** (SOC 2, GDPR, PCI-DSS) can be generated at any time from the audit log.

**Stack:** Python 3.13 · FastAPI · PostgreSQL · SQLAlchemy (async) · Alembic · Docker

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

> **Note on hash-chain integrity:** The demo runs two separate agent sessions. Because the audit log is scoped globally, events from session 2 interleave with session 1 in the chain — causing the integrity scan to report `COMPROMISED`. This is expected demo behaviour and demonstrates that the detection mechanism is working correctly.

```bash
────────────────────────────────────────────────────────────────
  SENTINEL  —  Agentic Audit & Compliance Layer  (POC Demo)
────────────────────────────────────────────────────────────────
Session : sess_a11dd2d9fa05
Authenticated as [u:abc]...
Tenant ID: 019d5f2b-3fbf-7342-945c-37f9a8464fb2
Agent ID: 019d5fa0-166f-7d30-9366-c999a6d923be

[1] Small payment: £50 GBP  →  expect ALLOW
    Decision : ✔ ALLOW
    Reason   : Payment within approved parameters — amount ≤ £500, currency approved

[2] Large payment: £800 GBP  →  expect ESCALATE → human APPROVES → ALLOW
    No pending escalation found!
    Decision : ✗ BLOCK
    Reason   : Escalation TIMEOUT — action blocked
    Escalation : 019d5fa0-16ec-7d33-aa43-c2d2b2e38e3a

[3] Payment in JPY (disallowed currency)  →  expect ESCALATE → REJECT → BLOCK
    No pending escalation found!
    Decision : ✗ BLOCK
    Reason   : Escalation TIMEOUT — action blocked
    Escalation : 019d5fa0-52ff-7813-a0c7-be46b93cbd65

[4] data.delete (bulk)  →  expect BLOCK (hard policy)
    Decision : ✗ BLOCK
    Reason   : Data mutations require direct human action — agents are not authorized

[5] email.send  →  expect ALLOW (default passthrough)
    Decision : ✔ ALLOW
    Reason   : Email dispatch is unrestricted for this agent

[6] Audit log (hash-chained)

  EVENT ID                      ACTION                          DECISION  PREV HASH
  ────────────────────────────  ──────────────────────────────  ────────  ────────────────────
  019d5fa0-b68d-7ac2-b777-449c  email.send                      ALLOW     10d79be614f7d21b20...
  019d5fa0-b62c-73a2-8a24-9d1d  data.delete                     BLOCK     dd80027fbcb83b79a0...
  019d5fa0-5316-7d02-a420-4a42  payments.initiate               BLOCK     b205bf301b5fd705b5... 👤
  019d5fa0-16f4-7631-bf75-5ac1  payments.initiate               BLOCK     ced336f2d21f331a00... 👤
  019d5fa0-16d9-7ca3-8ebc-7d6f  payments.initiate               ALLOW     e6b208bf028dae0431...
  019d5f9b-b2d6-7ef2-a000-5b48  email.send                      ALLOW     e00fc5556738cc430a...
  019d5f9b-b280-7411-ae38-44b9  data.delete                     BLOCK     fe73e4455bb0d39f55...
  019d5f9b-924c-7fb2-92d5-022d  payments.initiate               BLOCK     4d43c61b73e8fcd6ee... 👤
  019d5f9b-7228-7273-8afe-4c3f  payments.initiate               BLOCK     6d5cf0a710359aeea9... 👤
  019d5f9b-71fe-7602-916b-1ded  payments.initiate               ALLOW     4d3cc6f6bba531847a...

[7] Hash-chain integrity scan
    Chain    : ✗ COMPROMISED
    Checked  : 10 events
    Violations: [{'position': 0, 'event_id': '019d5fa0-b68d-7ac2-b777-449c5980a342', 'expected_prev_hash': '4d3cc6f6bba531847a989106d8c33f1bbf9a47974a9dadc95abaa76fe870219a', 'actual_prev_hash': '10d79be614f7d21b20f7e1da3c2559a94f5888c0dff88e6bdef3f55b796a3ee3'}, {'position': 1, 'event_id': '019d5fa0-b62c-73a2-8a24-9d1d1e898578', 'expected_prev_hash': 'bc6fc7d9620a82d198cc7b6be2248fd3de00ef1e6ecb84642d2d804bf37e68c4', 'actual_prev_hash': 'dd80027fbcb83b79a076fed17a26cf0460307a9d1ab319fe1907264cadfc09b1'}, {'position': 2, 'event_id': '019d5fa0-5316-7d02-a420-4a4277231764', 'expected_prev_hash': '10d79be614f7d21b20f7e1da3c2559a94f5888c0dff88e6bdef3f55b796a3ee3', 'actual_prev_hash': 'b205bf301b5fd705b52e3d322e78b7e2256c17b4096ce3b3be93721b7814a8f5'}, {'position': 3, 'event_id': '019d5fa0-16f4-7631-bf75-5ac1f463b090', 'expected_prev_hash': 'dd80027fbcb83b79a076fed17a26cf0460307a9d1ab319fe1907264cadfc09b1', 'actual_prev_hash': 'ced336f2d21f331a00eb17923d9132cf394b895add516771dd7e499397038b28'}, {'position': 4, 'event_id': '019d5fa0-16d9-7ca3-8ebc-7d6f092a4417', 'expected_prev_hash': 'b205bf301b5fd705b52e3d322e78b7e2256c17b4096ce3b3be93721b7814a8f5', 'actual_prev_hash': 'e6b208bf028dae0431b7920259942d7dcd839b62ea5feea2d17ff525ca735f9b'}, {'position': 5, 'event_id': '019d5f9b-b2d6-7ef2-a000-5b48ee523a5b', 'expected_prev_hash': 'ced336f2d21f331a00eb17923d9132cf394b895add516771dd7e499397038b28', 'actual_prev_hash': 'e00fc5556738cc430ae8cc79803a65bebc86c5f771fdc700257cf13fd0e42aee'}, {'position': 6, 'event_id': '019d5f9b-b280-7411-ae38-44b934c59f72', 'expected_prev_hash': 'e6b208bf028dae0431b7920259942d7dcd839b62ea5feea2d17ff525ca735f9b', 'actual_prev_hash': 'fe73e4455bb0d39f5544dc7a946cad7b1859d20f2fd080584920223793dd7f12'}, {'position': 7, 'event_id': '019d5f9b-924c-7fb2-92d5-022d974415a1', 'expected_prev_hash': 'e00fc5556738cc430ae8cc79803a65bebc86c5f771fdc700257cf13fd0e42aee', 'actual_prev_hash': '4d43c61b73e8fcd6ee0d6809902d2754fd3270d9b7af02ca9fe05c48ddd3adc0'}, {'position': 8, 'event_id': '019d5f9b-7228-7273-8afe-4c3f2ad65ae7', 'expected_prev_hash': 'fe73e4455bb0d39f5544dc7a946cad7b1859d20f2fd080584920223793dd7f12', 'actual_prev_hash': '6d5cf0a710359aeea92afb0a8d6c5db93b0c2e5a836caf2b2c665d0c65d8ea6a'}, {'position': 9, 'event_id': '019d5f9b-71fe-7602-916b-1ded97b723c6', 'expected_prev_hash': '4d43c61b73e8fcd6ee0d6809902d2754fd3270d9b7af02ca9fe05c48ddd3adc0', 'actual_prev_hash': '4d3cc6f6bba531847a989106d8c33f1bbf9a47974a9dadc95abaa76fe870219a'}]

[8] Compliance reports

  SOC 2 Type II — CC6
    Total actions  : 10
    Allowed        : 4
    Blocked        : 6  (60.0%)
    Escalated      : 4  (40.0%)
    Human approvals: 0   rejections: 0
    Chain integrity: ✗
    All agent actions were evaluated against a versioned declarative policy prior to execution. An append-only, hash-chained audit log was maintained for every action. High-risk actions were routed to a named human approver before execution. Audit chain integrity: VIOLATIONS DETECTED

  GDPR Article 30
    Data access events : 2
    Agents with access : ['019d5fa0-166f-7d30-9366-c999a6d923be', '019d5ee3-eb5b-79c0-8aaf-b7f6c9162e37']

  PCI-DSS Requirement 10
    Payment actions    : 6
    Allowed            : 2
    Blocked            : 4
    Human approved     : 0
    All payment-related agent actions were intercepted, policy-evaluated, and logged prior to execution. Actions exceeding the approved threshold were held for named human approval before proceeding. No payment action bypassed the Sentinel gateway.

────────────────────────────────────────────────────────────────
  POC COMPLETE
────────────────────────────────────────────────────────────────
  All Sentinel flows exercised successfully.

  Interactive API docs: http://localhost:4587/docs
```

## Next Steps

- [ ] Custom agent policies
- [ ] SDK implementation
    - [ ] Python - PYPI release
    - [ ] Typescript - NPM release
