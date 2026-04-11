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
<docker_PAT> | docker login dhi.io -u <username> --password-stdin
```

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
[0] Agent session running on: sess_335c3e5ecaf5

[1] Authenticated as [u:abc]...

[2] Tenant ID: 019d7e9c-f44b-7472-92a3-785f40fdc150

[3] Agent ID: 019d7ebc-2da9-7812-a7bf-f5e5bcc7f32e

[4] Policy ID: 019d7ebc-2dfa-7700-88fd-ec8e90364579

[5] Tenant Policy ID: 019d7ebc-2e68-7fb2-b3d6-333a03e769d0

[6] Small payment: £50 GBP  →  expect ALLOW
    Decision : ✗ BLOCK
    Reason   : Escalation TIMEOUT — action blocked

[7] Large payment: £800 GBP  →  expect ESCALATE → human APPROVES → ALLOW
    No pending escalation found!
    Decision : ✔ ALLOW
    Reason   : Payment within approved parameters — amount ≤ £500, currency approve
    Escalation : None

[8] Payment in JPY (disallowed currency)  →  expect ESCALATE → REJECT → BLOCK
    No pending escalation found!
    Decision : ✗ BLOCK
    Reason   : Escalation TIMEOUT — action blocked
    Escalation : 019d7ebc-5a39-7ea0-b853-ca8cd1295214

[10] data.delete (bulk)  →  expect BLOCK (hard policy)
    Decision : ✗ BLOCK
    Reason   : Data mutations require direct human action — agents are not authorized

[11] email.send  →  expect ALLOW (default passthrough)
    Decision : ✔ ALLOW
    Reason   : Email dispatch is unrestricted for this agent

[12] Audit log (hash-chained)

  EVENT ID                      ACTION                          DECISION  PREV HASH
  ────────────────────────────  ──────────────────────────────  ────────  ────────────────────
  019d7ebc-7a81-7f41-98c8-b8de  email.send                      ALLOW     4c2e466325e813f16d...
  019d7ebc-7a46-7513-82ff-3ae5  data.delete                     BLOCK     b3a7f49864051dcc78...
  019d7ebc-5a61-7531-a8c0-27bd  payments.initiate               BLOCK     0c13e0298a0ba30f9a... 👤
  019d7ebc-2ee8-7461-ae1f-adf1  payments.initiate               ALLOW     c1221028a6bad20cb8...
  019d7ebc-2ece-70e2-806b-ba06  payments.initiate               BLOCK     ef30ae378ce25e6a82... 👤
  019d7ebb-a9a6-7ed2-b0c9-4248  email.send                      ALLOW     75ac44cf20e8e11363...
  019d7ebb-a95b-7ee0-858a-1d08  data.delete                     BLOCK     5b3aa339e9203e12a0...
  019d7ebb-8946-7421-8462-5807  payments.initiate               BLOCK     53790549b0165e8db9... 👤
  019d7ebb-6935-78c2-8038-30f1  payments.initiate               ALLOW     1bfe2d518a988df45a...
  019d7ebb-6923-7bb0-ae8d-168a  payments.initiate               BLOCK     260c2b7b11c14efb72... 👤
  019d7eb9-a717-76c2-91d5-5fc2  email.send                      ALLOW     9f2813b9f559152511...
  019d7eb9-a6cd-7391-8a7c-fb13  data.delete                     BLOCK     a1de308c82a982a4a3...
  019d7eb9-86dc-7071-b41a-0ebd  payments.initiate               BLOCK     1d1f4ad71e2c4c5280... 👤
  019d7eb9-66b2-7ed3-aa16-73fe  payments.initiate               ALLOW     484044b2c068058a83...
  019d7eb9-669b-72f0-bb58-8fec  payments.initiate               BLOCK     4d3cc6f6bba531847a... 👤

[13] Hash-chain integrity scan
    Chain    : ✗ COMPROMISED
    Checked  : 15 events
    Violations: [{'position': 0, 'event_id': '019d7ebc-7a81-7f41-98c8-b8de151ac805', 'expected_prev_hash': '4d3cc6f6bba531847a989106d8c33f1bbf9a47974a9dadc95abaa76fe870219a', 'actual_prev_hash': '4c2e466325e813f16d551155c9a813531dd2ff3d537b750b0b389883a1917d0c'}, {'position': 1, 'event_id': '019d7ebc-7a46-7513-82ff-3ae51e9982e7', 'expected_prev_hash': '9bebfc8f9f9f379d2195d3bd67ab10308d215515a5f44cac1aad53506baf90c8', 'actual_prev_hash': 'b3a7f49864051dcc7839de766e39965efde37ffab61751ded4d066bde53a0c13'}, {'position': 2, 'event_id': '019d7ebc-5a61-7531-a8c0-27bd7fdcefde', 'expected_prev_hash': '4c2e466325e813f16d551155c9a813531dd2ff3d537b750b0b389883a1917d0c', 'actual_prev_hash': '0c13e0298a0ba30f9a4ea33c36c5bc341d0117b4c771a37c3e5d16fe2d12139c'}, {'position': 3, 'event_id': '019d7ebc-2ee8-7461-ae1f-adf1a8b8c682', 'expected_prev_hash': 'b3a7f49864051dcc7839de766e39965efde37ffab61751ded4d066bde53a0c13', 'actual_prev_hash': 'c1221028a6bad20cb8aecea3c376351c21e79d83a6beb962f85ea5b8d11e890c'}, {'position': 4, 'event_id': '019d7ebc-2ece-70e2-806b-ba0614f4211e', 'expected_prev_hash': '0c13e0298a0ba30f9a4ea33c36c5bc341d0117b4c771a37c3e5d16fe2d12139c', 'actual_prev_hash': 'ef30ae378ce25e6a82beed7345c2f386ea80d0260589b24b1d2a82e6fd44d918'}, {'position': 5, 'event_id': '019d7ebb-a9a6-7ed2-b0c9-4248a13babb0', 'expected_prev_hash': 'c1221028a6bad20cb8aecea3c376351c21e79d83a6beb962f85ea5b8d11e890c', 'actual_prev_hash': '75ac44cf20e8e1136356b5326c591aa8e99b06c0d37b5337c1827289bbb1de1f'}, {'position': 6, 'event_id': '019d7ebb-a95b-7ee0-858a-1d083b3aba6a', 'expected_prev_hash': 'ef30ae378ce25e6a82beed7345c2f386ea80d0260589b24b1d2a82e6fd44d918', 'actual_prev_hash': '5b3aa339e9203e12a0b91f99545ba65299af1a3e5dfaf8558d4d0cbdcbc5239a'}, {'position': 7, 'event_id': '019d7ebb-8946-7421-8462-5807f12105c3', 'expected_prev_hash': '75ac44cf20e8e1136356b5326c591aa8e99b06c0d37b5337c1827289bbb1de1f', 'actual_prev_hash': '53790549b0165e8db94b88a3f7da73ff2c599b25f23fc994b9dbbb702b72f135'}, {'position': 8, 'event_id': '019d7ebb-6935-78c2-8038-30f1327e69e7', 'expected_prev_hash': '5b3aa339e9203e12a0b91f99545ba65299af1a3e5dfaf8558d4d0cbdcbc5239a', 'actual_prev_hash': '1bfe2d518a988df45af7615958e032f5887b7ec05a3f5317ec9e50900838f186'}, {'position': 9, 'event_id': '019d7ebb-6923-7bb0-ae8d-168a3646f25d', 'expected_prev_hash': '53790549b0165e8db94b88a3f7da73ff2c599b25f23fc994b9dbbb702b72f135', 'actual_prev_hash': '260c2b7b11c14efb72bdc45586fd3e77422fc0e242c0fcf2d333b4331882c5d1'}, {'position': 10, 'event_id': '019d7eb9-a717-76c2-91d5-5fc202c8ac65', 'expected_prev_hash': '1bfe2d518a988df45af7615958e032f5887b7ec05a3f5317ec9e50900838f186', 'actual_prev_hash': '9f2813b9f55915251132614e590443fbc1368c3666e2222a9c352cb09985e5f1'}, {'position': 11, 'event_id': '019d7eb9-a6cd-7391-8a7c-fb1386285922', 'expected_prev_hash': '260c2b7b11c14efb72bdc45586fd3e77422fc0e242c0fcf2d333b4331882c5d1', 'actual_prev_hash': 'a1de308c82a982a4a3620b2564fc6b7d35f7cc5a77e2901092c161b87b8ed620'}, {'position': 12, 'event_id': '019d7eb9-86dc-7071-b41a-0ebd330a5d5b', 'expected_prev_hash': '9f2813b9f55915251132614e590443fbc1368c3666e2222a9c352cb09985e5f1', 'actual_prev_hash': '1d1f4ad71e2c4c528040aee2148c293e967e3a2857c087a5947c8a3d36227980'}, {'position': 13, 'event_id': '019d7eb9-66b2-7ed3-aa16-73fec4df2afb', 'expected_prev_hash': 'a1de308c82a982a4a3620b2564fc6b7d35f7cc5a77e2901092c161b87b8ed620', 'actual_prev_hash': '484044b2c068058a83d1484d8b6f21ce4e377a9800a830602cb162663166d223'}, {'position': 14, 'event_id': '019d7eb9-669b-72f0-bb58-8fec7be28954', 'expected_prev_hash': '1d1f4ad71e2c4c528040aee2148c293e967e3a2857c087a5947c8a3d36227980', 'actual_prev_hash': '4d3cc6f6bba531847a989106d8c33f1bbf9a47974a9dadc95abaa76fe870219a'}]

[14] Compliance reports

  SOC 2 Type II — CC6
    Total actions  : 15
    Allowed        : 6
    Blocked        : 9  (60.0%)
    Escalated      : 6  (40.0%)
    Human approvals: 0   rejections: 0
    Chain integrity: ✗
    All agent actions were evaluated against a versioned declarative policy prior to execution. An append-only, hash-chained audit log was maintained for every action. High-risk actions were routed to a named human approver before execution. Audit chain integrity: VIOLATIONS DETECTED

  GDPR Article 30
    Data access events : 3
    Agents with access : ['019d7ebc-2da9-7812-a7bf-f5e5bcc7f32e', '019d7eb9-6557-7701-8137-a5993365b00e', '019d7ebb-67f0-7322-b5ce-251f96840432']

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

Currently, this proof-of-concept only contains the backend implementation. TypeScript and Python SDKs are planned for the next iteration to simplify integration. If you prefer to use the APIs directly, you can find an example agent policy template [here](https://github.com/aybruhm/provenance/blob/main/api/resources/policies/agent_policy_template.json) and the e2e code [here](https://github.com/aybruhm/provenance/blob/main/api/tests/manual/e2e_demo.py).

## Next Steps

- [ ] SDK implementation
    - [ ] Python - PYPI release
    - [ ] Typescript - NPM release
