import { Decision, ExecutionResult } from "../core/models";

export interface ProvenanceSessionProtocol {
  guard(
    action?: string,
    options?: {
      decision?: Decision;
      raiseOnBlock?: boolean;
    },
  ): <T extends (...args: any[]) => any>(func: T) => T;

  execute(
    action: string,
    parameters: Record<string, any>,
    options?: {
      decision?: Decision;
    },
  ): ExecutionResult;

  asyncExecute(
    action: string,
    parameters: Record<string, any>,
    options?: {
      decision?: Decision;
    },
  ): Promise<ExecutionResult>;

  readonly results: ExecutionResult[];
  readonly blockedCount: number;
  readonly allowedCount: number;

  [Symbol.dispose](): void;
}
