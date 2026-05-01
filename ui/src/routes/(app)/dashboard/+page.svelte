<script lang="ts">
	import { session } from '$lib/stores/session';
	import { fetchAudit } from '$lib/controllers/audit';
	import { listPolicies } from '$lib/controllers/policies';
	import type { AuditEvent, Policy } from '$lib/types/index';
	import AuditTab from '$lib/components/AuditTab.svelte';
	import ReportsTab from '$lib/components/ReportsTab.svelte';
	import PolicyTab from '$lib/components/PolicyTab.svelte';
	import SimulatorTab from '$lib/components/SimulatorTab.svelte';
	import EscalationsTab from '$lib/components/EscalationsTab.svelte';

	type Tab = 'escalations' | 'audit' | 'reports' | 'policy' | 'simulator';

	let activeTab = $state<Tab>('escalations');
	let events = $state<AuditEvent[]>([]);
	let policies = $state<Policy[]>([]);
	let pollTimer: ReturnType<typeof setInterval> | null = null;

	const tabs: { key: Tab; label: string }[] = [
		{ key: 'escalations', label: 'Escalations' },
		{ key: 'audit', label: 'Audit Log' },
		{ key: 'reports', label: 'Compliance Reports' },
		{ key: 'policy', label: 'Policy' },
		{ key: 'simulator', label: 'Event Simulator' }
	];

	async function poll() {
		const { tenantId } = session.data;
		if (!tenantId) return;
		try {
			events = await fetchAudit(tenantId);
		} catch {
			// silently ignore
		}
	}

	async function loadPolicies() {
		const { tenantId } = session.data;
		if (!tenantId) return;
		try {
			policies = await listPolicies(tenantId);
		} catch {
			// silently ignore
		}
	}

	$effect(() => {
		poll();
		loadPolicies();
		pollTimer = setInterval(poll, 2000);
		return () => {
			if (pollTimer) clearInterval(pollTimer);
		};
	});
</script>

<div>
	<!-- Tabs -->
	<div class="mb-5 flex gap-0 border-b `border-(--border)">
		{#each tabs as tab}
			<button
				onclick={() => (activeTab = tab.key)}
				class="relative px-4 py-2.5 text-xs font-medium transition-colors {activeTab === tab.key
					? 'text-[var(--text)]'
					: 'text-[var(--muted)] hover:text-[var(--text)]'}"
			>
				{tab.label}
				{#if activeTab === tab.key}
					<span class="absolute inset-x-0 bottom-0 h-0.5 rounded-full bg-(--blue)"></span>
				{/if}
			</button>
		{/each}
	</div>

	<!-- Tab content -->
	{#if activeTab === 'escalations'}
		<EscalationsTab />
	{:else if activeTab === 'audit'}
		<AuditTab {events} />
	{:else if activeTab === 'reports'}
		<ReportsTab />
	{:else if activeTab === 'policy'}
		<PolicyTab {policies} onRefresh={loadPolicies} />
	{:else if activeTab === 'simulator'}
		<SimulatorTab />
	{/if}
</div>
