<script lang="ts">
	type Decision = 'ALLOW' | 'BLOCK' | 'ESCALATE' | 'INFO';

	let { decision }: { decision: Decision } = $props();

	const styles: Record<Decision, string> = {
		ALLOW: 'bg-[var(--green-dim)] text-[var(--green)]',
		BLOCK: 'bg-[var(--red-dim)] text-[var(--red)]',
		ESCALATE: 'bg-[var(--yellow-dim)] text-[var(--yellow)]',
		INFO: 'bg-[var(--blue-dim)] text-[var(--blue)]'
	};
</script>

<span
	class="inline-flex items-center rounded px-2 py-0.5 font-mono text-xs font-semibold tracking-wider {styles[decision] ?? styles.INFO}"
>
	{decision}
</span>
