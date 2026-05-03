import { envUtils } from '../../utils/env';
import { apiFetch } from '../../utils/request';

const API_BASE_URL = envUtils.getBaseUrl();

export async function createApiKey(userId: string, tenantPolicyId: string): Promise<string> {
	const resp = await apiFetch(`${API_BASE_URL}/api_keys/`, {
		method: 'POST',
		credentials: 'include',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ user_id: userId, scope_id: tenantPolicyId })
	});
	if (!resp.ok) {
		const err = await resp.json().catch(() => ({}));
		throw new Error(err?.detail?.message ?? 'Failed to create API key');
	}
	const data = await resp.json();
	return data.api_key;
}
