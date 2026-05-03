import { envUtils } from '../../utils/env';
import { apiFetch } from '../../utils/request';
import type { Tenant } from '$lib/types/index';

const API_BASE_URL = envUtils.getBaseUrl();

export async function listTenants(): Promise<Tenant[]> {
	const resp = await apiFetch(`${API_BASE_URL}/tenants/`, { credentials: 'include' });
	if (!resp.ok) throw new Error('Failed to list tenants');
	const data = await resp.json();
	return data.tenants ?? [];
}

export async function createTenant(name: string, policyId = ''): Promise<string> {
	const resp = await apiFetch(`${API_BASE_URL}/tenants/`, {
		method: 'POST',
		credentials: 'include',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ name, policy_id: policyId })
	});
	if (!resp.ok) {
		const err = await resp.json().catch(() => ({}));
		throw new Error(err?.detail?.message ?? 'Failed to create tenant');
	}
	const data = await resp.json();
	return data.tenant.id;
}
