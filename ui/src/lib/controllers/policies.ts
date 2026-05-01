import { envUtils } from '../../utils/env';
import { apiFetch } from '../../utils/request';
import type { Policy, PolicyRule } from '$lib/types/index';

const API_BASE_URL = envUtils.getBaseUrl();

export const DEFAULT_RULES: PolicyRule[] = [
	{
		action: 'data.*',
		reason: 'Data mutations require direct human action — agents are not authorized',
		on_match: 'BLOCK'
	},
	{
		action: 'payments.initiate',
		reason:
			'Currency not on the approved list [GBP, USD, EUR]. Escalating to compliance team for manual review.',
		conditions: [
			{ name: 'currency_check', field: 'currency', operator: 'in', value: ['GBP', 'USD', 'EUR'] }
		],
		on_violation: 'ESCALATE'
	},
	{
		action: 'payments.initiate',
		reason: 'Payment exceeds the £500 autonomous limit. Human approval required before execution.',
		conditions: [{ name: 'amount_check', field: 'amount', operator: '>=', value: 500 }],
		on_violation: 'ESCALATE'
	},
	{
		action: 'payments.initiate',
		reason: 'Payment within approved parameters — amount ≤ £500, currency approved',
		on_match: 'ALLOW'
	},
	{
		action: 'email.send',
		reason: 'Email dispatch is unrestricted for this agent',
		on_match: 'ALLOW'
	},
	{
		action: '*',
		reason: 'No specific policy rule matched; default block',
		on_match: 'BLOCK'
	}
];

export async function listPolicies(tenantId: string): Promise<Policy[]> {
	const resp = await apiFetch(`${API_BASE_URL}/policies/?tenant_id=${tenantId}`, {
		credentials: 'include'
	});
	if (!resp.ok) throw new Error('Failed to list policies');
	const data = await resp.json();
	return data.policies ?? [];
}

export async function getTenantPolicyId(
	policyId: string,
	tenantId: string
): Promise<string | null> {
	const resp = await apiFetch(`${API_BASE_URL}/policies/${policyId}?tenant_id=${tenantId}`, {
		credentials: 'include'
	});
	if (!resp.ok) return null;
	const data = await resp.json();
	return data.tenant_policy_id ?? null;
}

export async function createPolicy(
	name: string,
	description: string,
	rules: PolicyRule[],
	version = '0.1'
): Promise<string> {
	const resp = await apiFetch(`${API_BASE_URL}/policies/`, {
		method: 'POST',
		credentials: 'include',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ name, version, description, rules })
	});
	if (!resp.ok) {
		const err = await resp.json().catch(() => ({}));
		throw new Error(err?.detail?.message ?? 'Failed to create policy');
	}
	const data = await resp.json();
	return data.policy.id;
}

export async function updatePolicy(
	policyId: string,
	name: string,
	version: string,
	description: string,
	rules: PolicyRule[]
): Promise<Policy> {
	const resp = await apiFetch(`${API_BASE_URL}/policies/${policyId}`, {
		method: 'PUT',
		credentials: 'include',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ name, version, description, rules })
	});
	if (!resp.ok) {
		const err = await resp.json().catch(() => ({}));
		throw new Error(err?.detail?.message ?? 'Failed to update policy');
	}
	const data = await resp.json();
	return data.policy;
}

export async function assignPolicy(tenantId: string, policyId: string): Promise<string> {
	const check = await apiFetch(`${API_BASE_URL}/policies/${policyId}?tenant_id=${tenantId}`, {
		credentials: 'include'
	});
	const checkData = await check.json();
	if (!('detail' in checkData)) {
		return checkData.tenant_policy_id ?? '';
	}

	const resp = await apiFetch(`${API_BASE_URL}/policies/${policyId}/assign`, {
		method: 'POST',
		credentials: 'include',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ tenant_id: tenantId })
	});
	if (!resp.ok) {
		const err = await resp.json().catch(() => ({}));
		throw new Error(err?.detail?.message ?? 'Failed to assign policy');
	}
	const data = await resp.json();
	return data.tenant_policy_id;
}
