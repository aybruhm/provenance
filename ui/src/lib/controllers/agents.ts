import { envUtils } from '../../utils/env';
import { apiFetch } from '../../utils/request';
import type { Agent } from '$lib/types/index';

const API_BASE_URL = envUtils.getBaseUrl();

export async function listAgents(): Promise<Agent[]> {
	const resp = await apiFetch(`${API_BASE_URL}/agents/`, { credentials: 'include' });
	if (!resp.ok) throw new Error('Failed to list agents');
	const data = await resp.json();
	return data.agents ?? [];
}

export async function createAgent(tenantId: string, name: string): Promise<string> {
	const resp = await apiFetch(`${API_BASE_URL}/agents/`, {
		method: 'POST',
		credentials: 'include',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ tenant_id: tenantId, name })
	});
	if (!resp.ok) {
		const err = await resp.json().catch(() => ({}));
		throw new Error(err?.detail?.message ?? 'Failed to create agent');
	}
	const data = await resp.json();
	return data.agent.id;
}
