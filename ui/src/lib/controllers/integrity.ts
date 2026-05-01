import { envUtils } from '../../utils/env';
import { apiFetch } from '../../utils/request';
import type { IntegrityResult } from '$lib/types/index';

const API_BASE_URL = envUtils.getBaseUrl();

export async function runIntegrity(tenantId: string): Promise<IntegrityResult> {
	const resp = await apiFetch(`${API_BASE_URL}/audit/integrity/${tenantId}`, { credentials: 'include' });
	if (!resp.ok) throw new Error('Failed to run integrity scan');
	const data = await resp.json();
	return data.integrity;
}
