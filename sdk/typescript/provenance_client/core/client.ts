import axios, { AxiosInstance } from "axios";
import { v4 as uuidv4 } from "uuid";
import { Decision, ExecutionResult } from "./models";

export interface ProvenanceClientOptions {
  gatewayUrl: string;
  agentId: string;
  onGatewayError?: "closed" | "open";
  defaultSession?: string;
  timeout?: number;
  apiKey?: string;
}

export class ProvenanceClient {
  public readonly gatewayUrl: string;
  public readonly agentId: string;
  public readonly onGatewayError: "closed" | "open";
  public readonly defaultSession: string;
  public readonly timeout: number;
  public readonly apiKey?: string;

  private _httpClient?: AxiosInstance;

  constructor(options: ProvenanceClientOptions) {
    this.gatewayUrl = options.gatewayUrl.replace(/\/$/, "");
    this.agentId = options.agentId;
    this.onGatewayError = options.onGatewayError ?? "closed";
    this.defaultSession =
      options.defaultSession ??
      `sess_${uuidv4().replace(/-/g, "").substring(0, 16)}`;
    this.timeout = options.timeout ?? 90_000;
    this.apiKey = options.apiKey;
  }

  public get httpClient(): AxiosInstance {
    if (!this._httpClient) {
      this._httpClient = axios.create({
        baseURL: this.gatewayUrl,
        timeout: this.timeout,
        headers: this.apiKey ? { "X-PROVENANCE-API-KEY": this.apiKey } : {},
      });
    }
    return this._httpClient;
  }

  public buildPayload(
    action: string,
    parameters: Record<string, any>,
    sessionId: string,
    decision?: Decision,
  ): Record<string, any> {
    return {
      session_id: sessionId,
      agent_id: this.agentId,
      action,
      decision: decision ?? Decision.BLOCK,
      parameters,
    };
  }

  public parseResponse(data: any, action: string): ExecutionResult {
    return new ExecutionResult(
      data.decision as Decision,
      data.reason || "",
      action,
      data.event_id || "",
      data.escalation_id,
      data.actor_human_id,
    );
  }

  public failOpen(action: string, exc: Error): ExecutionResult {
    console.warn(
      `Provenance gateway unreachable (${exc.message}); failing open for '${action}'`,
    );
    return new ExecutionResult(
      Decision.ALLOW,
      "Gateway unavailable — fail-open policy applied",
      action,
      "",
    );
  }

  /** No-op: this SDK uses Node's default HTTP agent; no resources to release. */
  public async close(): Promise<void> {}
}
