export enum Decision {
  ALLOW = "ALLOW",
  BLOCK = "BLOCK",
  ESCALATE = "ESCALATE",
}

export class ExecutionResult {
  public readonly decision: Decision;
  public readonly reason: string;
  public readonly action: string;
  public readonly eventId: string;
  public readonly escalationId?: string;
  public readonly actorHumanId?: string;
  public toolResult?: any;

  constructor(
    decision: Decision,
    reason: string,
    action: string,
    eventId: string,
    escalationId?: string,
    actorHumanId?: string,
    toolResult?: any,
  ) {
    this.decision = decision;
    this.reason = reason;
    this.action = action;
    this.eventId = eventId;
    this.escalationId = escalationId;
    this.actorHumanId = actorHumanId;
    this.toolResult = toolResult;
  }

  get allowed(): boolean {
    return this.decision === Decision.ALLOW;
  }

  get blocked(): boolean {
    return this.decision === Decision.BLOCK;
  }

  get escalated(): boolean {
    return this.decision === Decision.ESCALATE;
  }
}
