<script lang="ts">
	import type { Escalation } from '$lib/types/index';

	let {
		escalation,
		onDecide
	}: {
		escalation: Escalation;
		onDecide: (id: string, decision: 'APPROVE' | 'REJECT', approver: string, reason: string) => void;
	} = $props();

	function relTime(ts: string) {
		const diff = Date.now() - new Date(ts).getTime();
		const mins = Math.floor(diff / 60000);
		if (mins < 1) return 'just now';
		if (mins < 60) return `${mins}m ago`;
		return `${Math.floor(mins / 60)}h ago`;
	}

	function handleApprove() {
		const approver = prompt('Approver ID', 'operator@acme.com');
		if (approver === null) return;
		const reason = prompt('Reason', 'Verified and approved') ?? 'Approved';
		onDecide(escalation.id, 'APPROVE', approver, reason);
	}

	function handleReject() {
		const approver = prompt('Approver ID', 'operator@acme.com');
		if (approver === null) return;
		const reason = prompt('Reason', 'Not authorized') ?? 'Rejected';
		onDecide(escalation.id, 'REJECT', approver, reason);
	}
</script>

<div class="rounded border border-[var(--yellow)] border-opacity-40 bg-[var(--surface2)] p-3">
	<div class="mb-2 flex items-center justify-between">
		<span class="font-mono text-xs font-semibold text-[var(--yellow)]">{escalation.action}</span>
		<span class="rounded bg-[var(--yellow-dim)] px-1.5 py-0.5 text-xs font-semibold text-[var(--yellow)]">PENDING</span>
	</div>
	<div class="mb-1 font-mono text-xs text-[var(--muted)]">
		{escalation.id.slice(0, 20)}…
	</div>
	<div class="mb-3 text-xs text-[var(--muted)]">
		<strong class="text-[var(--text)]">Agent:</strong>
		{escalation.agent_id.slice(0, 24)}… ·
		{relTime(escalation.created_at)}
	</div>
	<div class="flex gap-2">
		<button
			onclick={handleApprove}
			class="flex-1 rounded border border-[var(--green)] bg-[var(--green-dim)] px-3 py-1.5 text-xs font-semibold text-[var(--green)] transition-opacity hover:opacity-80"
		>
			Approve
		</button>
		<button
			onclick={handleReject}
			class="flex-1 rounded border border-[var(--red)] bg-[var(--red-dim)] px-3 py-1.5 text-xs font-semibold text-[var(--red)] transition-opacity hover:opacity-80"
		>
			Reject
		</button>
	</div>
</div>
