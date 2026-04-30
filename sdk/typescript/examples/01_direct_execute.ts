/**
 * Example 1: Direct execute (async)
 *
 * The most explicit pattern: call provenance.asyncExecute(...) before running any
 * agent action. The gateway evaluates the active policy and returns a decision.
 *
 * NOTE: In Node.js, making network requests synchronously isn't cleanly supported in native execution like it is in Python.
 * Using `asyncExecute` correctly awaits the underlying Promise returned by Axios, avoiding the
 * `TypeError: Cannot read properties of undefined` error since `response.data` is now correctly unwrapped
 * from the resolved Promise.
 */

import {
  Decision,
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

async function initiatePayment(
  amount: number,
  currency: string,
  recipientId: string,
): Promise<Record<string, any>> {
  try {
    const result = await provenance.asyncExecute(
      "payments.initiate",
      {
        amount,
        currency,
        recipientId,
      },
      {
        decision: Decision.ALLOW,
      },
    );
    console.log(`Decision: ${result.decision}`);
    console.log(`Reason: ${result.reason}`);
    return { status: "ok", eventId: result.eventId };
  } catch (error) {
    if (error instanceof PolicyBlockedError) {
      console.log(`Blocked: ${error.reason} (event=${error.eventId})`);
      return {};
    }
    throw error;
  }
}

async function dropUsers(): Promise<Record<string, any>> {
  try {
    const result = await provenance.asyncExecute(
      "data.delete",
      {
        table: "users",
        condition: "WHERE created_at < '2020-01-01'",
      },
      {
        decision: Decision.BLOCK,
      },
    );
    console.log(`Decision: ${result.decision}`);
    console.log(`Reason: ${result.reason}`);
    return { status: "ok", eventId: result.eventId };
  } catch (error) {
    if (error instanceof PolicyBlockedError) {
      console.log(`Blocked: ${error.reason} (event=${error.eventId})`);
      return {};
    }
    throw error;
  }
}

async function main(): Promise<void> {
  // Small payment — expect ALLOW
  console.log("--- £50 GBP ---");
  await initiatePayment(50, "GBP", "rec_abc123");

  // Hard-blocked action
  console.log("\n--- data.delete ---");
  await dropUsers();
}

main();
