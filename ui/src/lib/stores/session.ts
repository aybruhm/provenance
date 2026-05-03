import { writable, get } from 'svelte/store';

export interface AppSession {
	userId: string;
	username: string;
	accessToken: string;
	tenantId: string;
	tenantName: string;
	agentId: string;
	agentName: string;
	policyId: string;
	tenantPolicyId: string;
	apiKey: string;
}

const STORAGE_KEY = 'provenance_session';

function loadFromStorage(): Partial<AppSession> {
	if (typeof localStorage === 'undefined') return {};
	try {
		const raw = localStorage.getItem(STORAGE_KEY);
		return raw ? JSON.parse(raw) : {};
	} catch {
		return {};
	}
}

function saveToStorage(data: Partial<AppSession>) {
	if (typeof localStorage === 'undefined') return;
	localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

const _store = writable<Partial<AppSession>>(loadFromStorage());

export const session = {
	subscribe: _store.subscribe,
	get data(): Partial<AppSession> {
		return get(_store);
	},
	update(patch: Partial<AppSession>) {
		_store.update((s) => {
			const next = { ...s, ...patch };
			saveToStorage(next);
			return next;
		});
	},
	clear() {
		_store.set({});
		if (typeof localStorage !== 'undefined') {
			localStorage.removeItem(STORAGE_KEY);
		}
	},
	isAuthenticated(): boolean {
		return !!get(_store).userId;
	},
	getAccessToken(): string {
		return get(_store).accessToken ?? '';
	},
	isSetupComplete(): boolean {
		const s = get(_store);
		return !!(s.tenantId && s.agentId && s.tenantPolicyId);
	}
};
