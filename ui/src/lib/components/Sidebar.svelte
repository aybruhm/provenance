<script lang="ts">
	import { session } from '$lib/stores/session';
	import { toasts } from '$lib/stores/toast';
	import { fetchPendingEscalations, decide } from '$lib/controllers/escalations';
	import { runIntegrity } from '$lib/controllers/integrity';
	import type { Escalation, IntegrityResult } from '$lib/types/index';
	import { listTenants } from '$lib/controllers/tenants';
	import { listAgents } from '$lib/controllers/agents';
	import { listPolicies, getTenantPolicyId } from '$lib/controllers/policies';
	import type { Workspace } from '$lib/stores/session';
	import EscalationCard from './EscalationCard.svelte';

	let escalations = $state<Escalation[]>([]);
	let integrity = $state<IntegrityResult | null>(null);
	let scanningIntegrity = $state(false);
	let workspaces = $state<Workspace[]>([]);
	let switchingWorkspace = $state(false);

	$effect(() => {
		loadWorkspaces();
	});

	async function loadWorkspaces() {
		try {
			const [tenants, agents] = await Promise.all([listTenants(), listAgents()]);
			workspaces = tenants.flatMap((tenant) =>
				agents
					.filter((agent) => agent.tenant_id === tenant.id)
					.map((agent) => ({ tenant, agent }))
			);
		} catch {
			workspaces = [];
		}
	}

	async function switchWorkspace(event: Event) {
		const value = (event.currentTarget as HTMLSelectElement).value;
		const workspace = workspaces.find(
			({ tenant, agent }) => `${tenant.id}:${agent.id}` === value
		);
		if (!workspace) return;

		switchingWorkspace = true;
		try {
			const policies = await listPolicies(workspace.tenant.id);
			let policyId = '';
			let tenantPolicyId = '';
			if (policies.length > 0) {
				policyId = policies[0].id;
				tenantPolicyId =
					policies[0].tenant_policy_id ??
					(await getTenantPolicyId(policyId, workspace.tenant.id)) ??
					'';
			}
			session.update({
				tenantId: workspace.tenant.id,
				tenantName: workspace.tenant.name,
				agentId: workspace.agent.id,
				agentName: workspace.agent.name,
				policyId,
				tenantPolicyId,
				workspaces
			});
		} catch (e) {
			toasts.add(e instanceof Error ? e.message : 'Failed to switch workspace', 'err');
		} finally {
			switchingWorkspace = false;
		}
	}

	export async function refresh() {
		const { tenantId } = session.data;
		if (!tenantId) return;
		try {
			escalations = await fetchPendingEscalations(tenantId);
		} catch {
			// silently ignore poll errors
		}
	}

	async function handleDecide(
		id: string,
		decision: 'APPROVE' | 'REJECT',
		approver: string,
		reason: string
	) {
		try {
			await decide(id, decision, approver, reason);
			toasts.add(`Escalation ${decision === 'APPROVE' ? 'approved' : 'rejected'}`, 'ok');
			await refresh();
		} catch (e) {
			toasts.add(e instanceof Error ? e.message : 'Failed', 'err');
		}
	}

	async function handleScanIntegrity() {
		const { tenantId } = session.data;
		if (!tenantId) return;
		scanningIntegrity = true;
		try {
			integrity = await runIntegrity(tenantId);
		} catch (e) {
			toasts.add(e instanceof Error ? e.message : 'Scan failed', 'err');
		} finally {
			scanningIntegrity = false;
		}
	}
</script>

<aside class="`border-(--border) flex flex-col gap-0 overflow-y-auto border-l bg-[var(--surface)]">
	<!-- Escalation Queue -->
	<div class="`border-(--border) border-b">
		<div
			class="flex items-center justify-between px-4 py-3"
			style="position:sticky;top:0;background:var(--surface);z-index:1"
		>
			<span class="text-xs font-semibold tracking-wider text-[var(--muted)] uppercase">
				Escalation Queue
			</span>
			{#if escalations.length > 0}
				<span
					class="rounded-full bg-[var(--red-dim)] px-1.5 py-0.5 text-xs font-semibold text-[var(--red)]"
				>
					{escalations.length}
				</span>
			{/if}
		</div>
		<div class="flex flex-col gap-2 px-3 pb-3">
			{#if escalations.length === 0}
				<div class="py-4 text-center text-xs text-[var(--muted)]">No pending escalations</div>
			{:else}
				{#each escalations as esc (esc.id)}
					<EscalationCard escalation={esc} onDecide={handleDecide} />
				{/each}
			{/if}
		</div>
	</div>

	<!-- Workspace Info -->
	<div class="`border-(--border) border-b">
		<div class="px-4 py-3" style="position:sticky;top:0;background:var(--surface);z-index:1">
			<span class="text-xs font-semibold tracking-wider text-[var(--muted)] uppercase">
				Workspace
			</span>
		</div>
		<dl class="flex flex-col gap-2.5 px-4 pb-4 text-xs">
			<div>
				<dt class="mb-0.5 text-[var(--muted)]">Tenant</dt>
				<dd class="font-medium text-[var(--text)]">{$session.tenantName || '—'}</dd>
				{#if $session.tenantId}
					<dd class="mt-0.5 font-mono text-[10px] break-all text-[var(--muted)]">
						{$session.tenantId}
					</dd>
				{/if}
			</div>
			<div>
				<dt class="mb-0.5 text-[var(--muted)]">Agent</dt>
				{#if workspaces.length > 1}
					<select
						value={`${$session.tenantId ?? ''}:${$session.agentId ?? ''}`}
						onchange={switchWorkspace}
						disabled={switchingWorkspace}
						aria-label="Switch agent workspace"
						class="w-full rounded border `border-(--border) bg-[var(--surface2)] px-2 py-1.5 text-xs font-medium text-[var(--text)]"
					>
						{#each workspaces as workspace (`${workspace.tenant.id}:${workspace.agent.id}`)}
							<option value={`${workspace.tenant.id}:${workspace.agent.id}`}>
								{workspace.agent.name}
							</option>
						{/each}
					</select>
				{:else}
					<dd class="font-medium text-[var(--text)]">{$session.agentName || '—'}</dd>
				{/if}
				{#if $session.agentId}
					<dd class="mt-0.5 font-mono text-[10px] break-all text-[var(--muted)]">
						{$session.agentId}
					</dd>
				{/if}
			</div>
			<div>
				<dt class="mb-0.5 text-[var(--muted)]">Tenant Policy</dt>
				{#if $session.tenantPolicyId}
					<dd class="font-mono text-[10px] break-all text-[var(--muted)]">
						{$session.tenantPolicyId}
					</dd>
				{:else}
					<dd class="font-medium text-[var(--text)]">—</dd>
				{/if}
			</div>
		</dl>
	</div>

	<!-- Chain Integrity -->
	<div>
		<div
			class="flex items-center justify-between px-4 py-3"
			style="position:sticky;top:0;background:var(--surface);z-index:1"
		>
			<span class="text-xs font-semibold tracking-wider text-[var(--muted)] uppercase">
				Chain Integrity
			</span>
		</div>
		<div class="px-3 pb-3">
			<button
				onclick={handleScanIntegrity}
				disabled={scanningIntegrity}
				class="`border-(--border) mb-3 w-full rounded border px-3 py-2 text-xs text-[var(--muted)] transition-colors hover:border-[var(--blue)] hover:text-[var(--blue)] disabled:opacity-50"
			>
				{scanningIntegrity ? 'Scanning…' : 'Scan Now'}
			</button>
			{#if integrity}
				<div
					class="rounded border p-3 text-xs {integrity.valid
						? 'border-[var(--green)] bg-[var(--green-dim)]'
						: 'border-[var(--red)] bg-[var(--red-dim)]'}"
				>
					<div
						class="mb-1.5 font-semibold {integrity.valid
							? 'text-[var(--green)]'
							: 'text-[var(--red)]'}"
					>
						{integrity.valid ? '✔ Chain Valid' : '✗ Violations Found'}
					</div>
					<div class="text-[var(--muted)]">
						{integrity.events_checked} events checked
					</div>
					{#if integrity.violations.length > 0}
						<div class="mt-2 text-[var(--red)]">
							{integrity.violations.length} violation(s)
						</div>
					{/if}
				</div>
			{:else}
				<div class="py-2 text-center text-xs text-[var(--muted)]">Click to run integrity scan</div>
			{/if}
		</div>
	</div>
</aside>
