/**
 * Example 3: Session context manager
 *
 * Groups related calls under one session_id for audit and policy purposes.
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

async function main(): Promise<void> {
  using session = provenance.session("sess_checkout");

  try {
    await session.asyncExecute("payments.initiate", {
      amount: 50,
      currency: "GBP",
    });
    await session.asyncExecute("email.send", {
      to: "customer@example.com",
      template: "receipt",
    });
  } catch (error) {
    if (error instanceof PolicyBlockedError) {
      console.log(`Action blocked: ${error.reason} (event=${error.eventId})`);
    } else {
      console.log(`Action failed:`, error);
    }
  }

  console.log(`Session completed with ${session.results.length} actions`);
  console.log(
    `Allowed: ${session.allowedCount}, Blocked: ${session.blockedCount}`,
  );
}

main();
