import { envUtils } from '../../utils/env';
import { apiFetch } from '../../utils/request';
import type { Report, ReportFramework } from '$lib/types/index';

const API_BASE_URL = envUtils.getBaseUrl();

export async function loadReport(tenantId: string, framework: ReportFramework): Promise<Report> {
	const resp = await apiFetch(`${API_BASE_URL}/reports/${tenantId}/${framework}`, { credentials: 'include' });
	if (!resp.ok) throw new Error(`Failed to load ${framework} report`);
	const data = await resp.json();
	return data.report;
}
