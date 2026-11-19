<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { session, type Workspace } from '$lib/stores/session';
	import { listTenants } from '$lib/controllers/tenants';
	import { listAgents } from '$lib/controllers/agents';
	import { listPolicies, getTenantPolicyId } from '$lib/controllers/policies';

	let workspaces = $state<Workspace[]>([]);
	let loading = $state(true);
	let switching = $state(false);
	let error = $state('');

	onMount(async () => {
		try {
			const [tenants, agents] = await Promise.all([listTenants(), listAgents()]);
			workspaces = tenants.flatMap((tenant) =>
				agents
					.filter((agent) => agent.tenant_id === tenant.id)
					.map((agent) => ({ tenant, agent }))
			);
			session.update({ workspaces });
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load workspaces';
		} finally {
			loading = false;
		}
	});

	async function choose(workspace: Workspace) {
		switching = true;
		error = '';
		try {
			let policyId = '';
			let tenantPolicyId = '';
			const policies = await listPolicies(workspace.tenant.id);
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
			goto('/dashboard');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to open workspace';
		} finally {
			switching = false;
		}
	}
</script>

<div class="flex min-h-screen items-start justify-center bg-[var(--bg)] px-4 pt-16">
	<div class="w-full max-w-xl">
		<h1 class="mb-1 text-xl font-semibold text-[var(--text)]">Choose an agent workspace</h1>
		<p class="mb-6 text-xs text-[var(--muted)]">
			Each agent is currently represented as its own workspace.
		</p>

		{#if error}
			<div class="mb-4 rounded border border-[var(--red)] bg-[var(--red-dim)] px-3 py-2 text-xs text-[var(--red)]">
				{error}
			</div>
		{/if}

		<div class="grid gap-3">
			{#if loading}
				<div class="rounded-lg border `border-(--border) bg-[var(--surface)] p-6 text-sm text-[var(--muted)]">
					Loading workspaces…
				</div>
			{:else if workspaces.length === 0}
				<div class="rounded-lg border `border-(--border) bg-[var(--surface)] p-6">
					<p class="mb-4 text-sm text-[var(--muted)]">You do not have any agent workspaces yet.</p>
					<button
						onclick={() => goto('/setup')}
						class="rounded border border-[var(--blue)] bg-[var(--blue-dim)] px-3 py-2 text-sm font-semibold text-[var(--blue)]"
					>
						Create a workspace
					</button>
				</div>
			{:else}
				{#each workspaces as workspace (`${workspace.tenant.id}:${workspace.agent.id}`)}
					<button
						onclick={() => choose(workspace)}
						disabled={switching}
						class="`border-(--border) flex w-full items-center justify-between rounded-lg border bg-[var(--surface)] px-4 py-4 text-left transition-colors hover:border-[var(--blue)] disabled:opacity-50"
					>
						<div>
							<div class="text-sm font-semibold text-[var(--text)]">{workspace.agent.name}</div>
							<div class="mt-1 text-xs text-[var(--muted)]">Tenant: {workspace.tenant.name}</div>
						</div>
						<span class="text-xs font-semibold text-[var(--blue)]">Open →</span>
					</button>
				{/each}
			{/if}
		</div>
	</div>
</div>
