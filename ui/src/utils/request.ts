import { goto } from '$app/navigation';
import { session } from '$lib/stores/session';

export function setAccessTokenCookie(token: string) {
	document.cookie = `access_token=${token}; path=/; SameSite=Lax`;
}

export function restoreAccessTokenCookie() {
	const token = session.getAccessToken();
	if (token) setAccessTokenCookie(token);
}

export async function apiFetch(input: RequestInfo, init?: RequestInit): Promise<Response> {
	const resp = await fetch(input, init);
	if (resp.status === 401) {
		session.clear();
		await goto('/login');
	}
	return resp;
}
