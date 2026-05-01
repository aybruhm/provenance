import { envUtils } from '../../utils/env';
import { apiFetch } from '../../utils/request';
import type { Escalation } from '$lib/types/index';

const API_BASE_URL = envUtils.getBaseUrl();

export async function fetchPendingEscalations(tenantId: string): Promise<Escalation[]> {
	const resp = await apiFetch(`${API_BASE_URL}/escalations/pending?tenant_id=${tenantId}`, {
		credentials: 'include'
	});
	if (!resp.ok) throw new Error('Failed to fetch escalations');
	const data = await resp.json();
	return data.escalations ?? [];
}

export async function decide(
	escalationId: string,
	decision: 'APPROVE' | 'REJECT',
	approverId: string,
	reason: string
): Promise<void> {
	const resp = await apiFetch(`${API_BASE_URL}/escalations/${escalationId}/decide`, {
		method: 'POST',
		credentials: 'include',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ decision, approver_id: approverId, reason })
	});
	if (!resp.ok) {
		const err = await resp.json().catch(() => ({}));
		throw new Error(err?.detail?.message ?? 'Failed to submit decision');
	}
}
