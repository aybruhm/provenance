<script lang="ts">
	import { toasts } from '$lib/stores/toast';

	const typeStyles = {
		ok: 'border-l-[var(--green)] text-[var(--green)]',
		err: 'border-l-[var(--red)] text-[var(--red)]',
		inf: 'border-l-[var(--blue)] text-[var(--blue)]'
	};
</script>

<div class="fixed right-4 bottom-4 z-50 flex flex-col gap-2">
	{#each $toasts as toast (toast.id)}
		<div
			class="flex items-center gap-3 rounded border border-l-2 border-[var(--border)] bg-[var(--surface)] px-4 py-3 shadow-lg {typeStyles[
				toast.type
			]}"
		>
			<span class="text-[var(--text)]">{toast.message}</span>
			<button
				class="ml-2 text-[var(--muted)] hover:text-[var(--text)]"
				onclick={() => toasts.remove(toast.id)}
			>
				✕
			</button>
		</div>
	{/each}
</div>
