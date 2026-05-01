<script lang="ts">
	import { session } from '$lib/stores/session';
	import { toasts } from '$lib/stores/toast';
	import { goto } from '$app/navigation';
	import { createTenant } from '$lib/controllers/tenants';
	import { createAgent } from '$lib/controllers/agents';
	import { createPolicy, assignPolicy, DEFAULT_RULES } from '$lib/controllers/policies';
	import type { PolicyRule } from '$lib/types/index';
	import { createApiKey } from '$lib/controllers/apikeys';

	let step = $state(1);
	let loading = $state(false);
	let error = $state('');

	// Step 1: Tenant
	let tenantName = $state('');

	// Step 2: Agent
	let agentName = $state('');

	// Step 3: Policy
	let policyName = $state('');
	let policyDescription = $state('');
	let rulesJson = $state(JSON.stringify(DEFAULT_RULES, null, 2));

	// Step 4: API Key
	let apiKey = $state('');

	const steps = [
		{ n: 1, label: 'Create Tenant' },
		{ n: 2, label: 'Create Agent' },
		{ n: 3, label: 'Create Policy' },
		{ n: 4, label: 'Get API Key' }
	];

	async function submitTenant(e: Event) {
		e.preventDefault();
		error = '';
		loading = true;
		try {
			const tenantId = await createTenant(tenantName);
			session.update({ tenantId, tenantName });
			step = 2;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed';
			toasts.add(error, 'err');
		} finally {
			loading = false;
		}
	}

	async function submitAgent(e: Event) {
		e.preventDefault();
		error = '';
		loading = true;
		try {
			const { tenantId } = session.data;
			if (!tenantId) throw new Error('No tenant ID');
			const agentId = await createAgent(tenantId, agentName);
			session.update({ agentId, agentName });
			step = 3;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed';
			toasts.add(error, 'err');
		} finally {
			loading = false;
		}
	}

	async function submitPolicy(e: Event) {
		e.preventDefault();
		error = '';
		loading = true;
		try {
			const { tenantId } = session.data;
			if (!tenantId) throw new Error('No tenant ID');
			let rules: PolicyRule[];
			try {
				rules = JSON.parse(rulesJson);
			} catch {
				throw new Error('Invalid JSON in policy rules');
			}
			const policyId = await createPolicy(policyName, policyDescription, rules);
			const tenantPolicyId = await assignPolicy(tenantId, policyId);
			session.update({ policyId, tenantPolicyId });
			step = 4;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed';
			toasts.add(error, 'err');
		} finally {
			loading = false;
		}
	}

	async function generateApiKey() {
		error = '';
		loading = true;
		try {
			const { userId, tenantPolicyId } = session.data;
			if (!userId || !tenantPolicyId) throw new Error('Missing user or tenant policy ID');
			apiKey = await createApiKey(userId, tenantPolicyId);
			session.update({ apiKey });
			toasts.add('API key created — save it now, it will not be shown again', 'inf', 8000);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed';
			toasts.add(error, 'err');
		} finally {
			loading = false;
		}
	}

	function goToDashboard() {
		goto('/dashboard');
	}
</script>

<div class="flex min-h-screen items-start justify-center bg-[var(--bg)] px-4 pt-12">
	<div class="w-full max-w-xl">
		<!-- Header -->
		<div class="mb-8">
			<div class="mb-1 flex items-center gap-2">
				<div
					class="flex h-7 w-7 items-center justify-center rounded bg-(--blue) text-sm font-bold text-white"
				>
					P
				</div>
				<span class="text-sm font-semibold text-[var(--text)]">Provenance</span>
			</div>
			<h1 class="text-xl font-semibold text-[var(--text)]">Set up your workspace</h1>
			<p class="mt-1 text-xs text-[var(--muted)]">
				Complete the steps below to configure your tenant, agent, and policy.
			</p>
		</div>

		<!-- Steps indicator -->
		<div class="mb-6 flex gap-2">
			{#each steps as s (s.n)}
				<div class="flex flex-1 flex-col items-center gap-1">
					<div
						class="flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold {step >
						s.n
							? 'bg-(--green) text-white'
							: step === s.n
								? 'bg-(--blue) text-white'
								: 'bg-[var(--surface2)] text-[var(--muted)]'}"
					>
						{step > s.n ? '✓' : s.n}
					</div>
					<div class="text-center text-xs text-[var(--muted)]">{s.label}</div>
				</div>
				{#if s.n < 4}
					<div class="mt-3.5 h-px flex-1 bg-[var(--border)]"></div>
				{/if}
			{/each}
		</div>

		<!-- Card -->
		<div class="`border-(--border) rounded-lg border bg-[var(--surface)] p-6">
			{#if error}
				<div
					class="mb-4 rounded border border-[var(--red)] bg-[var(--red-dim)] px-3 py-2 text-xs text-[var(--red)]"
				>
					{error}
				</div>
			{/if}

			<!-- Step 1: Tenant -->
			{#if step === 1}
				<h2 class="mb-4 text-sm font-semibold text-[var(--text)]">Create Tenant</h2>
				<form onsubmit={submitTenant} class="flex flex-col gap-4">
					<div>
						<label for="setup-tenant" class="mb-1 block text-xs text-[var(--muted)]"
							>Tenant name</label
						>
						<input
							id="setup-tenant"
							type="text"
							bind:value={tenantName}
							required
							placeholder="e.g. acme"
							class="`border-(--border) w-full rounded border bg-[var(--surface2)] px-3 py-2 text-sm text-[var(--text)] placeholder-[var(--muted)] focus:border-[var(--blue)] focus:outline-none"
						/>
					</div>
					<button
						type="submit"
						disabled={loading}
						class="rounded border border-[var(--blue)] bg-[var(--blue-dim)] py-2 text-sm font-semibold text-[var(--blue)] hover:opacity-80 disabled:opacity-50"
					>
						{loading ? 'Creating…' : 'Create Tenant'}
					</button>
				</form>

				<!-- Step 2: Agent -->
			{:else if step === 2}
				<h2 class="mb-1 text-sm font-semibold text-[var(--text)]">Create Agent</h2>
				<p class="mb-4 text-xs text-[var(--muted)]">
					Tenant: <strong class="text-[var(--text)]">{session.data.tenantName}</strong>
				</p>
				<form onsubmit={submitAgent} class="flex flex-col gap-4">
					<div>
						<label for="setup-agent" class="mb-1 block text-xs text-[var(--muted)]"
							>Agent name</label
						>
						<input
							id="setup-agent"
							type="text"
							bind:value={agentName}
							required
							placeholder="e.g. payment_agent"
							class="`border-(--border) w-full rounded border bg-[var(--surface2)] px-3 py-2 text-sm text-[var(--text)] placeholder-[var(--muted)] focus:border-[var(--blue)] focus:outline-none"
						/>
					</div>
					<button
						type="submit"
						disabled={loading}
						class="rounded border border-[var(--blue)] bg-[var(--blue-dim)] py-2 text-sm font-semibold text-[var(--blue)] hover:opacity-80 disabled:opacity-50"
					>
						{loading ? 'Creating…' : 'Create Agent'}
					</button>
				</form>

				<!-- Step 3: Policy -->
			{:else if step === 3}
				<h2 class="mb-1 text-sm font-semibold text-[var(--text)]">Create Policy</h2>
				<p class="mb-4 text-xs text-[var(--muted)]">
					Define the rules that govern your agent's actions. Default rules are pre-filled.
				</p>
				<form onsubmit={submitPolicy} class="flex flex-col gap-4">
					<div class="grid grid-cols-2 gap-3">
						<div>
							<label for="setup-policy-name" class="mb-1 block text-xs text-[var(--muted)]"
								>Policy name</label
							>
							<input
								id="setup-policy-name"
								type="text"
								bind:value={policyName}
								required
								placeholder="e.g. payment_policy"
								class="`border-(--border) w-full rounded border bg-[var(--surface2)] px-3 py-2 text-sm text-[var(--text)] placeholder-[var(--muted)] focus:border-[var(--blue)] focus:outline-none"
							/>
						</div>
						<div>
							<label for="setup-policy-desc" class="mb-1 block text-xs text-[var(--muted)]"
								>Description</label
							>
							<input
								id="setup-policy-desc"
								type="text"
								bind:value={policyDescription}
								placeholder="optional description"
								class="`border-(--border) w-full rounded border bg-[var(--surface2)] px-3 py-2 text-sm text-[var(--text)] placeholder-[var(--muted)] focus:border-[var(--blue)] focus:outline-none"
							/>
						</div>
					</div>
					<div>
						<label for="setup-policy-rules" class="mb-1 block text-xs text-[var(--muted)]"
							>Rules (JSON)</label
						>
						<textarea
							id="setup-policy-rules"
							bind:value={rulesJson}
							rows={12}
							class="`border-(--border) w-full rounded border bg-[var(--surface2)] px-3 py-2 font-mono text-xs text-[var(--text)] focus:border-[var(--blue)] focus:outline-none"
						></textarea>
					</div>
					<button
						type="submit"
						disabled={loading}
						class="rounded border border-[var(--blue)] bg-[var(--blue-dim)] py-2 text-sm font-semibold text-[var(--blue)] hover:opacity-80 disabled:opacity-50"
					>
						{loading ? 'Creating…' : 'Create & Assign Policy'}
					</button>
				</form>

				<!-- Step 4: API Key -->
			{:else if step === 4}
				<h2 class="mb-1 text-sm font-semibold text-[var(--text)]">Generate API Key</h2>
				<p class="mb-4 text-xs text-[var(--muted)]">
					Your API key scopes gateway access to this tenant's policy. Store it securely — it won't
					be shown again.
				</p>
				{#if !apiKey}
					<button
						onclick={generateApiKey}
						disabled={loading}
						class="mb-4 w-full rounded border border-[var(--blue)] bg-[var(--blue-dim)] py-2 text-sm font-semibold text-[var(--blue)] hover:opacity-80 disabled:opacity-50"
					>
						{loading ? 'Generating…' : 'Generate API Key'}
					</button>
				{:else}
					<div class="mb-4 rounded border border-[var(--green)] bg-[var(--green-dim)] p-3">
						<div class="mb-1 text-xs font-semibold tracking-wider text-[var(--green)] uppercase">
							Your API Key
						</div>
						<div class="font-mono text-xs break-all text-[var(--text)]">{apiKey}</div>
					</div>
					<button
						onclick={goToDashboard}
						class="w-full rounded border border-[var(--blue)] bg-[var(--blue-dim)] py-2 text-sm font-semibold text-[var(--blue)] hover:opacity-80"
					>
						Go to Dashboard →
					</button>
				{/if}
			{/if}
		</div>
	</div>
</div>
