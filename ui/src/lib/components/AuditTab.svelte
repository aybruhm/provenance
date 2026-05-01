<script lang="ts">
	import Badge from './Badge.svelte';
	import type { AuditEvent } from '$lib/types/index';

	let { events }: { events: AuditEvent[] } = $props();

	const total = $derived(events.length);
	const allow = $derived(events.filter((e) => e.decision === 'ALLOW').length);
	const block = $derived(events.filter((e) => e.decision === 'BLOCK').length);
	const escalate = $derived(events.filter((e) => e.decision === 'ESCALATE').length);

	function relTime(ts: string) {
		const diff = Date.now() - new Date(ts).getTime();
		const secs = Math.floor(diff / 1000);
		if (secs < 60) return `${secs}s ago`;
		const mins = Math.floor(secs / 60);
		if (mins < 60) return `${mins}m ago`;
		return `${Math.floor(mins / 60)}h ago`;
	}

	function short(s: string, n = 12) {
		return s ? s.slice(0, n) + '…' : '—';
	}

	const reversed = $derived([...events].reverse());
</script>

<div>
	<!-- Stats -->
	<div class="mb-4 grid grid-cols-4 gap-3">
		<div class="`border-(--border) rounded border bg-[var(--surface)] p-4 text-center">
			<div class="text-2xl font-bold text-[var(--blue)]">{total}</div>
			<div class="mt-0.5 text-xs text-[var(--muted)]">Total</div>
		</div>
		<div class="`border-(--border) rounded border bg-[var(--surface)] p-4 text-center">
			<div class="text-2xl font-bold text-[var(--green)]">{allow}</div>
			<div class="mt-0.5 text-xs text-[var(--muted)]">Allowed</div>
		</div>
		<div class="`border-(--border) rounded border bg-[var(--surface)] p-4 text-center">
			<div class="text-2xl font-bold text-[var(--red)]">{block}</div>
			<div class="mt-0.5 text-xs text-[var(--muted)]">Blocked</div>
		</div>
		<div class="`border-(--border) rounded border bg-[var(--surface)] p-4 text-center">
			<div class="text-2xl font-bold text-[var(--yellow)]">{escalate}</div>
			<div class="mt-0.5 text-xs text-[var(--muted)]">Escalated</div>
		</div>
	</div>

	<!-- Table -->
	<div class="`border-(--border) overflow-hidden rounded border">
		{#if events.length === 0}
			<div class="py-12 text-center text-sm text-[var(--muted)]">
				No audit events yet. Fire an event from the simulator.
			</div>
		{:else}
			<table class="w-full">
				<thead>
					<tr class="`border-(--border) border-b bg-[var(--surface)]">
						<th
							class="px-4 py-3 text-left text-xs font-semibold tracking-wider text-[var(--muted)] uppercase"
							>Decision</th
						>
						<th
							class="px-4 py-3 text-left text-xs font-semibold tracking-wider text-[var(--muted)] uppercase"
							>Action</th
						>
						<th
							class="px-4 py-3 text-left text-xs font-semibold tracking-wider text-[var(--muted)] uppercase"
							>Agent</th
						>
						<th
							class="px-4 py-3 text-left text-xs font-semibold tracking-wider text-[var(--muted)] uppercase"
							>Session</th
						>
						<th
							class="px-4 py-3 text-left text-xs font-semibold tracking-wider text-[var(--muted)] uppercase"
							>Hash</th
						>
						<th
							class="px-4 py-3 text-left text-xs font-semibold tracking-wider text-[var(--muted)] uppercase"
							>Time</th
						>
					</tr>
				</thead>
				<tbody>
					{#each reversed as event (event.id)}
						<tr class="`border-(--border) border-b transition-colors hover:bg-[var(--surface2)]">
							<td class="px-4 py-3">
								<Badge decision={event.decision} />
							</td>
							<td class="px-4 py-3 font-mono text-xs text-[var(--text)]">{event.action}</td>
							<td class="px-4 py-3 font-mono text-xs text-[var(--muted)]"
								>{short(event.agent_id)}</td
							>
							<td class="px-4 py-3 font-mono text-xs text-[var(--muted)]"
								>{short(event.session_id)}</td
							>
							<td class="px-4 py-3 font-mono text-xs text-[var(--muted)]"
								>{short(event.prev_hash, 10)}</td
							>
							<td class="px-4 py-3 text-xs text-[var(--muted)]">{relTime(event.timestamp)}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		{/if}
	</div>
</div>
