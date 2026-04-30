import { Decision, ExecutionResult } from "./models";
import { ProvenanceGateway } from "./gateway";
import { ProvenanceSessionProtocol } from "../interfaces/session";

export class ProvenanceSession implements ProvenanceSessionProtocol {
  public readonly sessionId: string;
  private readonly gateway: ProvenanceGateway;
  private readonly _results: ExecutionResult[] = [];

  constructor(gateway: ProvenanceGateway, sessionId: string) {
    this.gateway = gateway;
    this.sessionId = sessionId;
  }

  public execute(
    action: string,
    parameters: Record<string, any>,
    options: {
      decision?: Decision;
    } = {},
  ): ExecutionResult {
    throw new Error(
      "Synchronous execution is not supported for ProvenanceSession. Use asyncExecute() instead.",
    );
  }

  public async asyncExecute(
    action: string,
    parameters: Record<string, any>,
    options: {
      decision?: Decision;
    } = {},
  ): Promise<ExecutionResult> {
    const result = await this.gateway.asyncExecute(action, parameters, {
      sessionId: this.sessionId,
      decision: options.decision,
    });
    this._results.push(result);
    return result;
  }

  public guard(
    action?: string,
    options: {
      decision?: Decision;
      raiseOnBlock?: boolean;
    } = {},
  ): <T extends (...args: any[]) => any>(func: T) => T {
    return this.gateway.guard(action, {
      ...options,
      sessionId: this.sessionId,
    });
  }

  public get results(): ExecutionResult[] {
    return [...this._results];
  }

  public get blockedCount(): number {
    return this._results.filter((r) => r.blocked).length;
  }

  public get allowedCount(): number {
    return this._results.filter((r) => r.allowed).length;
  }

  public [Symbol.dispose](): void {
    console.log(
      `Session ${this.sessionId} completed with ${this._results.length} results`,
    );
  }

  public toString(): string {
    return `ProvenanceSession(id=${this.sessionId}, results=${this._results.length})`;
  }
}
