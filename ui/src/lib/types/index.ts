// Auth
export interface UserData {
	id: string;
	username: string;
	accessToken: string;
}

// Tenants
export interface Tenant {
	id: string;
	name: string;
}

// Agents
export interface Agent {
	id: string;
	name: string;
	tenant_id: string;
}

// Policies
export interface PolicyCondition {
	name: string;
	field: string;
	operator: string;
	value: unknown;
}

export interface PolicyRule {
	action: string;
	reason: string;
	on_match?: string;
	on_violation?: string;
	conditions?: PolicyCondition[];
}

export interface Policy {
	id: string;
	name: string;
	description: string;
	version: string;
	rules: PolicyRule[];
	tenant_policy_id?: string;
}

// Audit
export type Decision = 'ALLOW' | 'BLOCK' | 'ESCALATE';

export interface AuditEvent {
	id: string;
	decision: Decision;
	action: string;
	agent_id: string;
	session_id: string;
	actor_human_id: string | null;
	prev_hash: string;
	timestamp: string;
	escalation_id: string | null;
}

// Escalations
export interface Escalation {
	id: string;
	action: string;
	agent_id: string;
	status: 'PENDING' | 'APPROVED' | 'REJECTED';
	created_at: string;
	approver_id: string | null;
	reason: string | null;
}

// Integrity
export interface IntegrityViolation {
	position: number;
	event_id: string;
	expected_prev_hash: string;
	actual_prev_hash: string;
}

export interface IntegrityResult {
	valid: boolean;
	events_checked: number;
	violations: IntegrityViolation[];
}

// Reports
export type ReportFramework = 'soc2' | 'gdpr' | 'pci';

export interface Report {
	framework: string;
	control?: string;
	report_generated_at: string;
	summary: Record<string, unknown>;
	audit_chain_integrity: { valid: boolean; events_checked: number };
	attestation: string;
	lawful_basis_note?: string;
}

// Gateway
export interface GatewayResult {
	decision: Decision;
	reason: string;
	event_id: string;
	escalation_id: string | null;
}

export interface Scenario {
	label: string;
	action: string;
	decision: string;
	parameters: Record<string, unknown>;
}
