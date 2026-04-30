import axios from "axios";
import { v4 as uuidv4 } from "uuid";
import { Decision, ExecutionResult } from "./models";
import { ProvenanceClient } from "./client";
import { ProvenanceSession } from "./session";
import { GatewayError, PolicyBlockedError } from "../services/exceptions";
import { ProvenanceGatewayProtocol } from "../interfaces/gateway";

const PROVENANCE_ATTR = "_provenance_guarded";

export class ProvenanceGateway implements ProvenanceGatewayProtocol {
  constructor(private client: ProvenanceClient) {}

  public toString(): string {
    return `ProvenanceGateway(cl=${this.client.gatewayUrl}, agent=${this.client.agentId})`;
  }

  public async asyncExecute(
    action: string,
    parameters: Record<string, any>,
    options: {
      sessionId?: string;
      decision?: Decision;
    } = {},
  ): Promise<ExecutionResult> {
    const sessionId = options.sessionId ?? this.client.defaultSession;
    const payload = this.client.buildPayload(
      action,
      parameters,
      sessionId,
      options.decision,
    );

    try {
      const response = await this.client.httpClient.post(
        "/v1/gateway/execute",
        payload,
      );
      const result = this.client.parseResponse(response.data, action);
      if (result.blocked) {
        throw new PolicyBlockedError(action, result.reason, result.eventId);
      }
      return result;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (this.client.onGatewayError === "open") {
          return this.client.failOpen(action, error);
        }
        throw new GatewayError(this.client.gatewayUrl, error);
      }
      throw error;
    }
  }

  public guard(
    action?: string,
    options: {
      sessionId?: string;
      decision?: Decision;
      raiseOnBlock?: boolean;
    } = {},
  ): <T extends (...args: any[]) => any>(
    func: T,
  ) => (...args: Parameters<T>) => Promise<Awaited<ReturnType<T>> | null> {
    return <T extends (...args: any[]) => any>(
      func: T,
    ): ((...args: Parameters<T>) => Promise<Awaited<ReturnType<T>> | null>) => {
      const resolvedAction =
        action ??
        `${(func as any).__module__ ?? "unknown"}.${(func as any).__qualname__ ?? func.name}`;
      const raiseOnBlock = options.raiseOnBlock ?? true;

      const extractParams = (args: any[]): Record<string, any> => {
        const params: Record<string, any> = {};
        try {
          const fnStr = func
            .toString()
            .replace(/((\/\/.*$)|(\/\*[\s\S]*?\*\/))/gm, "");
          const match = fnStr.match(/^[^\(]*\(\s*([^\)]*)\)/m);
          const paramNames = match
            ? match[1]
                .split(",")
                .map((s) => s.trim().split(/[ =\:]/)[0])
                .filter(Boolean)
            : [];

          for (let i = 0; i < args.length; i++) {
            const name = paramNames[i] || `arg${i}`;
            params[name] = args[i];
          }
        } catch (e) {
          for (let i = 0; i < args.length; i++) {
            params[`arg${i}`] = args[i];
          }
        }
        return params;
      };

      const self = this;
      const asyncWrapper = async function (
        this: ThisParameterType<T>,
        ...args: Parameters<T>
      ): Promise<Awaited<ReturnType<T>> | null> {
        const params = extractParams(args);
        try {
          const result = await self.asyncExecute(resolvedAction, params, {
            sessionId: options.sessionId,
            decision: options.decision,
          });
          const toolResult = await Promise.resolve(func.apply(this, args));
          result.toolResult = toolResult;
          return toolResult;
        } catch (error) {
          if (error instanceof PolicyBlockedError && !raiseOnBlock) {
            return null;
          }
          throw error;
        }
      };

      const wrapper = asyncWrapper;
      (wrapper as any)[PROVENANCE_ATTR] = true;
      (wrapper as any)._provenance_action = resolvedAction;
      return wrapper;
    };
  }

  public session(sessionId?: string): ProvenanceSession {
    return new ProvenanceSession(
      this,
      sessionId ?? `sess_${uuidv4().replace(/-/g, "").substring(0, 16)}`,
    );
  }
}
