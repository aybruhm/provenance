/**
 * Example 4: Human escalation
 *
 * Two policy rules trigger escalation for `payments.initiate`:
 *
 *   1. amount_check   — amount >= 500 → ESCALATE
 *   2. currency_check — currency not in [GBP, USD, EUR] → ESCALATE
 *
 * When either condition is violated the gateway raises EscalationError instead
 * of running the action.  The agent must pause, surface the escalation ID to a
 * human reviewer, and only proceed once approved via the dashboard or API.
 *
 * Reviewing escalations:
 *   1. Log in to the Provenance dashboard to view and action pending escalations.
 *   2. Create a new account or use your existing credentials to setup your workspace (or access an existing one if you already have it).
 *   3. Upon logging in, you'll be navigated to the "Escalations" tab to see any pending reviews. You can approve or reject escalations directly from the dashboard, and the agent will receive the outcome to proceed accordingly.
 */

import {
  Decision,
  ProvenanceClient,
  ProvenanceGateway,
  PolicyBlockedError,
  EscalationError,
  EscalationTimeoutError,
} from "../provenance_client/index";

const GATEWAY_URL = "http://localhost:4587";
const API_KEY = "pk_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx";

const provenance = new ProvenanceGateway(
  new ProvenanceClient({
    gatewayUrl: GATEWAY_URL,
    agentId: "xxxxxx-xxxx-xxxx-xxxx-xxxxxx",
    apiKey: API_KEY,
  }),
);

async function initiatePayment(
  amount: number,
  currency: string,
  recipientId: string,
): Promise<Record<string, any>> {
  try {
    const result = await provenance.asyncExecute(
      "payments.initiate",
      { amount, currency, recipientId },
      { decision: Decision.ESCALATE },
    );
    console.log(`Decision : ${result.decision}`);
    console.log(`Reason   : ${result.reason}`);
    return { status: "ok", eventId: result.eventId };
  } catch (error) {
    if (error instanceof EscalationError) {
      // Gateway has flagged this action for human review before it can proceed.
      // Store the escalationId and wait — do NOT execute the payment.
      console.log(
        `Escalated: action='${error.action}'  escalationId=${error.escalationId}`,
      );
      console.log("  → Payment paused. Awaiting human approval in the dashboard.");
      return { status: "pending", escalationId: error.escalationId };
    }

    if (error instanceof EscalationTimeoutError) {
      // No reviewer responded within the hold window — treat as blocked.
      console.log(
        `Timeout  : escalation for '${error.action}' expired  (esc=${error.escalationId})`,
      );
      console.log("  → Payment cancelled due to review timeout.");
      return { status: "cancelled", escalationId: error.escalationId };
    }

    if (error instanceof PolicyBlockedError) {
      console.log(`Blocked  : ${error.reason}  (event=${error.eventId})`);
      return { status: "blocked", eventId: error.eventId };
    }

    throw error;
  }
}

async function main(): Promise<void> {
  // Triggers amount_check: amount >= 500 → ESCALATE
  console.log("--- £800 GBP (amount exceeds autonomous limit) ---");
  await initiatePayment(800, "GBP", "rec_xyz789");

  console.log();

  // Triggers currency_check: JPY not in approved list → ESCALATE
  console.log("--- ¥10000 JPY (currency not on approved list) ---");
  await initiatePayment(10_000, "JPY", "rec_jpy001");

  console.log();

  // Both rules satisfied: amount < 500, currency approved → ALLOW
  console.log("--- £50 GBP (within policy — expect ALLOW) ---");
  await initiatePayment(50, "GBP", "rec_abc123");
}

main();
