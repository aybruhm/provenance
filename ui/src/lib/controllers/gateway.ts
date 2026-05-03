import { envUtils } from '../../utils/env';
import { apiFetch } from '../../utils/request';
import type { GatewayResult, Scenario } from '$lib/types/index';

const API_BASE_URL = envUtils.getBaseUrl();

export const SCENARIOS: Record<string, Scenario> = {
	small_payment: {
		label: 'Small payment £50 GBP',
		action: 'payments.initiate',
		decision: 'ALLOW',
		parameters: { amount: 50, currency: 'GBP', recipient_id: 'rec_abc123' }
	},
	large_payment: {
		label: 'Large payment £800 GBP',
		action: 'payments.initiate',
		decision: 'ESCALATE',
		parameters: { amount: 800, currency: 'GBP', recipient_id: 'rec_xyz789' }
	},
	bad_currency: {
		label: 'Payment in JPY (disallowed)',
		action: 'payments.initiate',
		decision: 'ESCALATE',
		parameters: { amount: 100, currency: 'JPY', recipient_id: 'rec_jpy001' }
	},
	data_delete: {
		label: 'data.delete (blocked)',
		action: 'data.delete',
		decision: 'BLOCK',
		parameters: { table: 'users', condition: "WHERE created_at < '2020-01-01'" }
	},
	email_send: {
		label: 'email.send (allowed)',
		action: 'email.send',
		decision: 'ALLOW',
		parameters: { to: 'customer@example.com', template: 'invoice_ready' }
	}
};

export async function fireEvent(
	agentId: string,
	tenantPolicyId: string,
	action: string,
	decision: string,
	parameters: Record<string, unknown>,
	sessionId?: string
): Promise<GatewayResult> {
	const sid = sessionId ?? `sess_${Math.random().toString(36).slice(2, 14)}`;
	const resp = await apiFetch(`${API_BASE_URL}/gateway/execute`, {
		method: 'POST',
		credentials: 'include',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({
			session_id: sid,
			agent_id: agentId,
			tenant_policy_id: tenantPolicyId,
			action,
			decision,
			parameters
		})
	});
	if (!resp.ok) {
		const err = await resp.json().catch(() => ({}));
		throw new Error(err?.detail?.message ?? 'Gateway execute failed');
	}
	return resp.json();
}
