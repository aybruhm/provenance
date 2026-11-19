<script lang="ts">
	import { login } from '$lib/controllers/auth';
	import { listTenants } from '$lib/controllers/tenants';
	import { listAgents } from '$lib/controllers/agents';
	import { listPolicies, getTenantPolicyId } from '$lib/controllers/policies';
	import { session } from '$lib/stores/session';
	import { toasts } from '$lib/stores/toast';
	import { setAccessTokenCookie } from '../../utils/request';
	import { goto } from '$app/navigation';

	let username = $state('');
	let password = $state('');
	let loading = $state(false);
	let error = $state('');

	async function restoreWorkspace() {
		const tenants = await listTenants();
		if (tenants.length === 0) return;

		const agents = await listAgents();
		const workspaces = tenants.flatMap((tenant) =>
			agents
				.filter((agent) => agent.tenant_id === tenant.id)
				.map((agent) => ({ tenant, agent }))
		);

		session.update({ workspaces });
		if (workspaces.length === 0) {
			const tenant = tenants[0];
			session.update({ tenantId: tenant.id, tenantName: tenant.name });
			return;
		}

		const workspace =
			workspaces.find(
				(workspace) =>
					workspace.agent.id === session.data.agentId &&
					workspace.tenant.id === session.data.tenantId
			) ?? workspaces[0];

		await selectWorkspace(workspace.tenant.id, workspace.tenant.name, workspace.agent.id, workspace.agent.name);
	}

	async function selectWorkspace(
		tenantId: string,
		tenantName: string,
		agentId: string,
		agentName: string
	) {
		session.update({ tenantId, tenantName, agentId, agentName });
		const policies = await listPolicies(tenantId);
		if (policies.length > 0) {
			const policy = policies[0];
			const tenantPolicyId =
				policy.tenant_policy_id ?? (await getTenantPolicyId(policy.id, tenantId));
			session.update({ policyId: policy.id, tenantPolicyId: tenantPolicyId ?? '' });
		} else {
			session.update({ policyId: '', tenantPolicyId: '' });
		}
	}

	async function handleSubmit(e: Event) {
		e.preventDefault();
		error = '';
		loading = true;
		try {
			const user = await login(username, password);
			session.update({ userId: user.id, username: user.username, accessToken: user.accessToken });
			setAccessTokenCookie(user.accessToken);
			try {
				await restoreWorkspace();
			} catch {
				// ignore — user will go through setup if needed
			}
			const workspaceCount = session.data.workspaces?.length ?? 0;
			goto(workspaceCount > 0 ? '/workspaces' : session.isSetupComplete() ? '/dashboard' : '/setup');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Login failed';
			toasts.add(error, 'err');
		} finally {
			loading = false;
		}
	}
</script>

<form onsubmit={handleSubmit} class="flex flex-col gap-4">
	<div>
		<label for="login-username" class="mb-1 block text-xs text-[var(--muted)]">Username</label>
		<input
			id="login-username"
			type="text"
			bind:value={username}
			required
			autocomplete="username"
			class="w-full rounded border `border-(--border) bg-[var(--surface2)] px-3 py-2 text-sm text-[var(--text)] placeholder-[var(--muted)] focus:border-[var(--blue)] focus:outline-none"
			placeholder="your username"
		/>
	</div>
	<div>
		<label for="login-password" class="mb-1 block text-xs text-[var(--muted)]">Password</label>
		<input
			id="login-password"
			type="password"
			bind:value={password}
			required
			autocomplete="current-password"
			class="w-full rounded border `border-(--border) bg-[var(--surface2)] px-3 py-2 text-sm text-[var(--text)] placeholder-[var(--muted)] focus:border-[var(--blue)] focus:outline-none"
			placeholder="••••••••"
		/>
	</div>
	{#if error}
		<div
			class="rounded border border-[var(--red)] bg-[var(--red-dim)] px-3 py-2 text-xs text-[var(--red)]"
		>
			{error}
		</div>
	{/if}
	<button
		type="submit"
		disabled={loading}
		class="rounded border border-[var(--blue)] bg-[var(--blue-dim)] py-2 text-sm font-semibold text-[var(--blue)] transition-opacity hover:opacity-80 disabled:opacity-50"
	>
		{loading ? 'Signing in…' : 'Sign in'}
	</button>
</form>
