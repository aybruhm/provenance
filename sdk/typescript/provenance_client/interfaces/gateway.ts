import { Decision, ExecutionResult } from "../core/models";

export interface ProvenanceGatewayProtocol {
  guard(
    action?: string,
    options?: {
      sessionId?: string;
      decision?: Decision;
      raiseOnBlock?: boolean;
    },
  ): <T extends (...args: any[]) => any>(
    func: T,
  ) => (...args: Parameters<T>) => Promise<Awaited<ReturnType<T>>>;

  execute(
    action: string,
    parameters: Record<string, any>,
    options?: {
      sessionId?: string;
      decision?: Decision;
    },
  ): ExecutionResult;

  asyncExecute(
    action: string,
    parameters: Record<string, any>,
    options?: {
      sessionId?: string;
      decision?: Decision;
    },
  ): Promise<ExecutionResult>;
}
