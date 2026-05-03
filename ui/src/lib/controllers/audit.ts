import { envUtils } from '../../utils/env';
import { apiFetch } from '../../utils/request';
import type { AuditEvent } from '$lib/types/index';

const API_BASE_URL = envUtils.getBaseUrl();

export async function fetchAudit(tenantId: string): Promise<AuditEvent[]> {
	const resp = await apiFetch(`${API_BASE_URL}/audit/${tenantId}`, { credentials: 'include' });
	if (!resp.ok) throw new Error('Failed to fetch audit log');
	const data = await resp.json();
	return data.events ?? [];
}
