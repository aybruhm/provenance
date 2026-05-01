<script lang="ts">
	import { session } from '$lib/stores/session';
	import { toasts } from '$lib/stores/toast';
	import { fetchPendingEscalations, decide } from '$lib/controllers/escalations';
	import type { Escalation } from '$lib/types/index';

	let escalations = $state<Escalation[]>([]);
	let loading = $state(true);
	let pollTimer: ReturnType<typeof setInterval> | null = null;

	// Per-card review state keyed by escalation id
	let reviewing = $state<Record<string, { approver: string; reason: string; submitting: boolean }>>(
		{}
	);

	async function load() {
		const { tenantId } = session.data;
		if (!tenantId) return;
		try {
			const raw = await fetchPendingEscalations(tenantId);
			escalations = raw.sort(
				(a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
			);
		} catch {
			// silently ignore poll errors
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		load();
		pollTimer = setInterval(load, 5000);
		return () => {
			if (pollTimer) clearInterval(pollTimer);
		};
	});

	function startReview(id: string) {
		reviewing = {
			...reviewing,
			[id]: { approver: session.data.username ?? '', reason: '', submitting: false }
		};
	}

	function cancelReview(id: string) {
		const next = { ...reviewing };
		delete next[id];
		reviewing = next;
	}

	async function submitDecision(id: string, decision: 'APPROVE' | 'REJECT') {
		const state = reviewing[id];
		if (!state) return;

		reviewing = { ...reviewing, [id]: { ...state, submitting: true } };
		try {
			await decide(id, decision, state.approver, state.reason);
			toasts.add(`Escalation ${decision === 'APPROVE' ? 'approved' : 'rejected'}`, 'ok');
			const next = { ...reviewing };
			delete next[id];
			reviewing = next;
			await load();
		} catch (e) {
			toasts.add(e instanceof Error ? e.message : 'Failed', 'err');
			reviewing = { ...reviewing, [id]: { ...state, submitting: false } };
		}
	}

	function relTime(ts: string) {
		const diff = Date.now() - new Date(ts).getTime();
		const mins = Math.floor(diff / 60000);
		if (mins < 1) return 'just now';
		if (mins < 60) return `${mins}m ago`;
		return `${Math.floor(mins / 60)}h ago`;
	}
</script>

<div>
	<!-- Header -->
	<div class="mb-5 flex items-center justify-between">
		<div>
			<h2 class="text-sm font-semibold text-[var(--text)]">Pending Escalations</h2>
			<p class="mt-0.5 text-xs text-[var(--muted)]">
				Actions flagged for human review before proceeding.
			</p>
		</div>
		{#if escalations.length > 0}
			<span
				class="rounded-full bg-[var(--yellow-dim)] px-2.5 py-1 text-xs font-semibold text-[var(--yellow)]"
			>
				{escalations.length} pending
			</span>
		{/if}
	</div>

	<!-- List -->
	{#if loading}
		<div class="py-12 text-center text-xs text-[var(--muted)]">Loading…</div>
	{:else if escalations.length === 0}
		<div class="`border-(--border) rounded border bg-[var(--surface)] px-6 py-12 text-center">
			<div class="mb-1 text-sm font-medium text-[var(--text)]">No pending escalations</div>
			<div class="text-xs text-[var(--muted)]">All agent actions are within policy bounds.</div>
		</div>
	{:else}
		<div class="flex flex-col gap-3">
			{#each escalations as esc (esc.id)}
				{@const rev = reviewing[esc.id]}
				<div
					class="border-opacity-30 rounded border border-[var(--yellow)] bg-[var(--surface)] p-4"
				>
					<!-- Top row -->
					<div class="mb-3 flex items-start justify-between gap-4">
						<div class="min-w-0 flex-1">
							<div class="mb-1 flex items-center gap-2">
								<span
									class="rounded bg-[var(--yellow-dim)] px-1.5 py-0.5 text-xs font-semibold tracking-wide text-[var(--yellow)] uppercase"
								>
									PENDING
								</span>
								<span class="font-mono text-xs font-semibold text-[var(--text)]">{esc.action}</span>
							</div>
							<div class="grid grid-cols-2 gap-x-6 gap-y-1 text-xs text-[var(--muted)]">
								<div>
									<span class="mr-1">Agent:</span>
									<span class="font-mono text-[var(--text)]" title={esc.agent_id}>
										{esc.agent_id.slice(0, 20)}…
									</span>
								</div>
								<div>
									<span class="mr-1">Received:</span>
									<span class="text-[var(--text)]">{relTime(esc.created_at)}</span>
								</div>
								<div class="col-span-2">
									<span class="mr-1">ID:</span>
									<span class="font-mono text-[var(--muted)]">{esc.id}</span>
								</div>
							</div>
						</div>
						{#if !rev}
							<button
								onclick={() => startReview(esc.id)}
								class="shrink-0 rounded border border-[var(--blue)] bg-[var(--blue-dim)] px-3 py-1.5 text-xs font-semibold text-[var(--blue)] transition-opacity hover:opacity-80"
							>
								Review
							</button>
						{/if}
					</div>

					<!-- Inline review form -->
					{#if rev}
						<div class="`border-(--border) border-t pt-3">
							<div class="mb-3 grid grid-cols-2 gap-3">
								<div>
									<label for="esc-approver-{esc.id}" class="mb-1 block text-xs text-[var(--muted)]">
										Approver ID
									</label>
									<input
										id="esc-approver-{esc.id}"
										type="text"
										value={rev.approver}
										disabled
										class="`border-(--border) w-full cursor-not-allowed rounded border bg-[var(--surface2)] px-2.5 py-1.5 text-xs text-[var(--muted)] opacity-60"
									/>
								</div>
								<div>
									<label for="esc-reason-{esc.id}" class="mb-1 block text-xs text-[var(--muted)]">
										Reason
									</label>
									<input
										id="esc-reason-{esc.id}"
										type="text"
										bind:value={rev.reason}
										placeholder="e.g. Verified by compliance team"
										class="`border-(--border) w-full rounded border bg-[var(--surface2)] px-2.5 py-1.5 text-xs text-[var(--text)] placeholder-[var(--muted)] focus:border-[var(--blue)] focus:outline-none"
									/>
								</div>
							</div>
							<div class="flex gap-2">
								<button
									onclick={() => submitDecision(esc.id, 'APPROVE')}
									disabled={rev.submitting || !rev.approver || !rev.reason}
									class="flex-1 rounded border border-[var(--green)] bg-[var(--green-dim)] py-1.5 text-xs font-semibold text-[var(--green)] transition-opacity hover:opacity-80 disabled:opacity-40"
								>
									{rev.submitting ? 'Submitting…' : 'Approve'}
								</button>
								<button
									onclick={() => submitDecision(esc.id, 'REJECT')}
									disabled={rev.submitting || !rev.approver || !rev.reason}
									class="flex-1 rounded border border-[var(--red)] bg-[var(--red-dim)] py-1.5 text-xs font-semibold text-[var(--red)] transition-opacity hover:opacity-80 disabled:opacity-40"
								>
									{rev.submitting ? 'Submitting…' : 'Reject'}
								</button>
								<button
									onclick={() => cancelReview(esc.id)}
									disabled={rev.submitting}
									class="`border-(--border) rounded border px-3 py-1.5 text-xs text-[var(--muted)] transition-colors hover:text-[var(--text)] disabled:opacity-40"
								>
									Cancel
								</button>
							</div>
						</div>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>
