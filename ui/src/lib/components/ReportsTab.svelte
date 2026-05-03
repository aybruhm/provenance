<script lang="ts">
	import { session } from '$lib/stores/session';
	import { toasts } from '$lib/stores/toast';
	import { loadReport } from '$lib/controllers/reports';
	import type { Report, ReportFramework } from '$lib/types/index';

	let activeFramework = $state<ReportFramework | null>(null);
	let report = $state<Report | null>(null);
	let loading = $state(false);

	const frameworks: { key: ReportFramework; label: string }[] = [
		{ key: 'soc2', label: 'SOC 2 Type II' },
		{ key: 'gdpr', label: 'GDPR Article 30' },
		{ key: 'pci', label: 'PCI-DSS Req. 10' }
	];

	async function fetchReport(framework: ReportFramework) {
		const { tenantId } = session.data;
		if (!tenantId) return;
		activeFramework = framework;
		loading = true;
		report = null;
		try {
			report = await loadReport(tenantId, framework);
		} catch (e) {
			toasts.add(e instanceof Error ? e.message : 'Failed to load report', 'err');
		} finally {
			loading = false;
		}
	}

	function formatKey(k: string) {
		return k.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
	}
</script>

<div>
	<div class="mb-4 flex gap-2">
		{#each frameworks as fw}
			<button
				onclick={() => fetchReport(fw.key)}
				class="rounded border px-4 py-2 text-xs font-semibold transition-colors {activeFramework ===
				fw.key
					? 'border-[var(--blue)] bg-[var(--blue-dim)] text-[var(--blue)]'
					: '`border-(--border) text-[var(--muted)] hover:border-[var(--blue)] hover:text-[var(--blue)]'}"
			>
				{fw.label}
			</button>
		{/each}
	</div>

	{#if loading}
		<div class="py-12 text-center text-sm text-[var(--muted)]">Generating report…</div>
	{:else if report}
		<div class="mb-3 flex items-center justify-between">
			<div class="text-sm font-semibold text-[var(--text)]">
				{report.framework ?? activeFramework?.toUpperCase()}
			</div>
			<div class="text-xs text-[var(--muted)]">
				{new Date(report.report_generated_at).toLocaleString()}
			</div>
		</div>

		<!-- Summary cards -->
		<div class="mb-4 grid grid-cols-2 gap-3 lg:grid-cols-3">
			{#each Object.entries(report.summary) as [key, val]}
				<div class="`border-(--border) rounded border bg-[var(--surface)] p-3">
					<div class="text-xs text-[var(--muted)]">{formatKey(key)}</div>
					<div class="mt-1 text-lg font-bold text-[var(--text)]">{val}</div>
				</div>
			{/each}
			<div class="`border-(--border) rounded border bg-[var(--surface)] p-3">
				<div class="text-xs text-[var(--muted)]">Chain Integrity</div>
				<div
					class="mt-1 text-lg font-bold {report.audit_chain_integrity?.valid
						? 'text-[var(--green)]'
						: 'text-[var(--red)]'}"
				>
					{report.audit_chain_integrity?.valid ? '✔ Valid' : '✗ Violated'}
				</div>
			</div>
		</div>

		<!-- Attestation -->
		<div
			class="`border-(--border) rounded border bg-[var(--surface)] p-4 text-xs text-[var(--muted)]"
		>
			{report.attestation}
		</div>

		{#if report.lawful_basis_note}
			<div
				class="`border-(--border) mt-2 rounded border bg-[var(--surface)] p-4 text-xs text-[var(--muted)]"
			>
				{report.lawful_basis_note}
			</div>
		{/if}
	{:else}
		<div class="py-12 text-center text-sm text-[var(--muted)]">
			Select a framework above to generate a compliance report.
		</div>
	{/if}
</div>
