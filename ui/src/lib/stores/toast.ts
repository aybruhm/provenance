import { writable } from 'svelte/store';

export type ToastType = 'ok' | 'err' | 'inf';

export interface ToastMessage {
	id: number;
	message: string;
	type: ToastType;
}

let _counter = 0;

function createToastStore() {
	const { subscribe, update } = writable<ToastMessage[]>([]);

	return {
		subscribe,
		add(message: string, type: ToastType = 'inf', duration = 3500) {
			const id = ++_counter;
			update((list) => [...list, { id, message, type }]);
			setTimeout(() => {
				update((list) => list.filter((t) => t.id !== id));
			}, duration);
		},
		remove(id: number) {
			update((list) => list.filter((t) => t.id !== id));
		}
	};
}

export const toasts = createToastStore();
