export class ProvenanceError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ProvenanceError";
  }
}

export class EscalationError extends ProvenanceError {
  public readonly action: string;
  public readonly escalationId: string;

  constructor(action: string, escalationId: string) {
    super(
      `[ESCALATE] Escalation in progress for '${action}' (esc=${escalationId})`,
    );
    this.name = "EscalationError";
    this.action = action;
    this.escalationId = escalationId;
  }
}

export class PolicyBlockedError extends ProvenanceError {
  public readonly action: string;
  public readonly reason: string;
  public readonly eventId: string;

  constructor(action: string, reason: string, eventId: string) {
    super(`[BLOCK] ${action}: ${reason} (event=${eventId})`);
    this.name = "PolicyBlockedError";
    this.action = action;
    this.reason = reason;
    this.eventId = eventId;
  }
}

export class EscalationTimeoutError extends ProvenanceError {
  public readonly action: string;
  public readonly escalationId: string;

  constructor(action: string, escalationId: string) {
    super(
      `[TIMEOUT] Escalation for '${action}' timed out (esc=${escalationId})`,
    );
    this.name = "EscalationTimeoutError";
    this.action = action;
    this.escalationId = escalationId;
  }
}

export class GatewayError extends ProvenanceError {
  public readonly url: string;
  public readonly cause: Error;

  constructor(url: string, cause: Error) {
    super(`Sentinel gateway unreachable at ${url}: ${cause.message}`);
    this.name = "GatewayError";
    this.url = url;
    this.cause = cause;
  }
}
