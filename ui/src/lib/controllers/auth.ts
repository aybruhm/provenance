import { envUtils } from '../../utils/env';
import type { UserData } from '$lib/types/index';

const API_BASE_URL = envUtils.getBaseUrl();

export async function register(username: string, password: string): Promise<UserData> {
	const resp = await fetch(`${API_BASE_URL}/auth/register`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		credentials: 'include',
		body: JSON.stringify({ username, password })
	});
	if (!resp.ok) {
		const err = await resp.json().catch(() => ({}));
		throw new Error(err?.detail?.message ?? 'Registration failed');
	}
	const data = await resp.json();
	return {
		id: data.user.id,
		username: data.user.username,
		accessToken: data.credentials.access_token
	};
}

export async function login(username: string, password: string): Promise<UserData> {
	const resp = await fetch(`${API_BASE_URL}/auth/login`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		credentials: 'include',
		body: JSON.stringify({ username, password })
	});
	if (!resp.ok) {
		const err = await resp.json().catch(() => ({}));
		throw new Error(err?.detail?.message ?? 'Login failed');
	}
	const data = await resp.json();
	return {
		id: data.user.id,
		username: data.user.username,
		accessToken: data.credentials.access_token
	};
}
