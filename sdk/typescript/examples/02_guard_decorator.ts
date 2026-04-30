/**
 * Example 2: @guard decorator (async)
 *
 * Wrap any callable with @provenance.guard("action") to intercept it before
 * execution. Provenance evaluates the policy; if allowed, the function runs
 * normally. If blocked, PolicyBlockedError is raised before the function body
 * is ever entered.
 */

import {
  ProvenanceClient,
  ProvenanceGateway,
  PolicyBlockedError,
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

// ── async guard ───────────────────────────────────────────────────────────────

const guardedInitiatePayment = provenance.guard("payments.initiate")(
  async function initiatePayment(
    amount: number,
    currency: string,
    recipientId: string,
  ): Promise<Record<string, any>> {
    // Only reached if Provenance allows it
    return { status: "initiated", amount, currency };
  },
);

const guardedSendEmail = provenance.guard("email.send")(
  async function sendEmail(
    to: string,
    template: string,
  ): Promise<Record<string, any>> {
    return { status: "sent", to };
  },
);

// ── main ──────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  console.log("--- Async: £50 GBP (expect ALLOW) ---");
  try {
    const result = await guardedInitiatePayment(50, "GBP", "rec_abc123");
    console.log(`Result: ${JSON.stringify(result)}`);
  } catch (error) {
    if (error instanceof PolicyBlockedError) {
      console.log(`Action blocked: ${error.reason} (event=${error.eventId})`);
    } else {
      console.log("Error:", error);
    }
  }

  console.log("\n--- Async: email.send (expect ALLOW) ---");
  try {
    const result = await guardedSendEmail(
      "customer@example.com",
      "invoice_ready",
    );
    console.log(`Result: ${JSON.stringify(result)}`);
  } catch (error) {
    if (error instanceof PolicyBlockedError) {
      console.log(`Action blocked: ${error.reason} (event=${error.eventId})`);
    } else {
      console.log("Error:", error);
    }
  }
}

main();
