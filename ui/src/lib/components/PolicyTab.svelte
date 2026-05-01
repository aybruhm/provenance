<script lang="ts">
	import { toasts } from '$lib/stores/toast';
	import { updatePolicy } from '$lib/controllers/policies';
	import type { Policy, PolicyRule } from '$lib/types/index';

	let { policies, onRefresh }: { policies: Policy[]; onRefresh: () => void } = $props();

	// Edit state
	let editingId = $state<string | null>(null);
	let editName = $state('');
	let editVersion = $state('');
	let editDescription = $state('');
	let editRulesJson = $state('');
	let saving = $state(false);
	let jsonError = $state('');

	function startEdit(policy: Policy) {
		editingId = policy.id;
		editName = policy.name;
		editVersion = policy.version;
		editDescription = policy.description ?? '';
		editRulesJson = JSON.stringify(policy.rules, null, 2);
		jsonError = '';
	}

	function cancelEdit() {
		editingId = null;
		jsonError = '';
	}

	async function saveEdit(policy: Policy) {
		jsonError = '';
		let rules: PolicyRule[];
		try {
			rules = JSON.parse(editRulesJson);
		} catch {
			jsonError = 'Invalid JSON — fix the rules before saving.';
			return;
		}
		saving = true;
		try {
			await updatePolicy(policy.id, editName, editVersion, editDescription, rules);
			editingId = null;
			toasts.add('Policy updated', 'ok');
			onRefresh();
		} catch (e) {
			toasts.add(e instanceof Error ? e.message : 'Failed to update policy', 'err');
		} finally {
			saving = false;
		}
	}

	const decisionColor: Record<string, string> = {
		ALLOW: 'text-[var(--green)]',
		BLOCK: 'text-[var(--red)]',
		ESCALATE: 'text-[var(--yellow)]'
	};

	function ruleDecision(rule: PolicyRule) {
		return rule.on_match ?? rule.on_violation ?? 'UNKNOWN';
	}

	function ruleDecisionLabel(rule: PolicyRule) {
		if (rule.on_match) return `on_match → ${rule.on_match}`;
		if (rule.on_violation) return `on_violation → ${rule.on_violation}`;
		return '';
	}
</script>

<div>
	{#if policies.length === 0}
		<div class="py-12 text-center text-sm text-[var(--muted)]">
			No policies found for this tenant.
		</div>
	{:else}
		{#each policies as policy (policy.id)}
			<div class="mb-4">
				<!-- Policy header -->
				<div class="mb-3 flex items-center gap-3">
					<span class="text-sm font-semibold text-[var(--text)]">{policy.name}</span>
					<span
						class="rounded bg-[var(--surface2)] px-1.5 py-0.5 font-mono text-xs text-[var(--muted)]"
					>
						v{policy.version}
					</span>
					{#if policy.description}
						<span class="text-xs text-[var(--muted)]">{policy.description}</span>
					{/if}
					<div class="flex-1"></div>
					{#if editingId !== policy.id}
						<button
							onclick={() => startEdit(policy)}
							class="rounded border border-[var(--border)] px-2.5 py-1 text-xs text-[var(--muted)] transition-colors hover:border-[var(--blue)] hover:text-[var(--blue)]"
						>
							Edit
						</button>
					{/if}
				</div>

				<!-- Edit mode -->
				{#if editingId === policy.id}
					<div
						class="border-opacity-40 rounded border border-[var(--blue)] bg-[var(--surface)] p-4"
					>
						<div class="mb-3 grid grid-cols-3 gap-3">
							<div>
								<label for="policy-name-{policy.id}" class="mb-1 block text-xs text-[var(--muted)]"
									>Name</label
								>
								<input
									id="policy-name-{policy.id}"
									type="text"
									bind:value={editName}
									class="w-full rounded border border-[var(--border)] bg-[var(--surface2)] px-2.5 py-1.5 text-xs text-[var(--text)] focus:border-[var(--blue)] focus:outline-none"
								/>
							</div>
							<div>
								<label
									for="policy-version-{policy.id}"
									class="mb-1 block text-xs text-[var(--muted)]">Version</label
								>
								<input
									id="policy-version-{policy.id}"
									type="text"
									bind:value={editVersion}
									class="w-full rounded border border-[var(--border)] bg-[var(--surface2)] px-2.5 py-1.5 text-xs text-[var(--text)] focus:border-[var(--blue)] focus:outline-none"
								/>
							</div>
							<div>
								<label for="policy-desc-{policy.id}" class="mb-1 block text-xs text-[var(--muted)]"
									>Description</label
								>
								<input
									id="policy-desc-{policy.id}"
									type="text"
									bind:value={editDescription}
									placeholder="optional"
									class="w-full rounded border border-[var(--border)] bg-[var(--surface2)] px-2.5 py-1.5 text-xs text-[var(--text)] placeholder-[var(--muted)] focus:border-[var(--blue)] focus:outline-none"
								/>
							</div>
						</div>
						<div class="mb-3">
							<label for="policy-rules-{policy.id}" class="mb-1 block text-xs text-[var(--muted)]"
								>Rules (JSON)</label
							>
							<textarea
								id="policy-rules-{policy.id}"
								bind:value={editRulesJson}
								rows={16}
								class="w-full rounded border border-[var(--border)] bg-[var(--surface2)] px-2.5 py-2 font-mono text-xs text-[var(--text)] focus:border-[var(--blue)] focus:outline-none"
							></textarea>
							{#if jsonError}
								<div class="mt-1 text-xs text-[var(--red)]">{jsonError}</div>
							{/if}
						</div>
						<div class="flex gap-2">
							<button
								onclick={() => saveEdit(policy)}
								disabled={saving}
								class="rounded border border-[var(--blue)] bg-[var(--blue-dim)] px-4 py-1.5 text-xs font-semibold text-[var(--blue)] transition-opacity hover:opacity-80 disabled:opacity-50"
							>
								{saving ? 'Saving…' : 'Save changes'}
							</button>
							<button
								onclick={cancelEdit}
								disabled={saving}
								class="rounded border border-[var(--border)] px-4 py-1.5 text-xs text-[var(--muted)] transition-colors hover:text-[var(--text)] disabled:opacity-50"
							>
								Cancel
							</button>
						</div>
					</div>

					<!-- View mode -->
				{:else}
					<div class="flex flex-col gap-2">
						{#each policy.rules as rule, i (i)}
							<div class="rounded border border-[var(--border)] bg-[var(--surface)] p-3">
								<div class="mb-1.5 flex items-center gap-3">
									<span class="font-mono text-xs text-[var(--purple)]">{rule.action}</span>
									<span
										class="font-mono text-xs font-semibold {decisionColor[ruleDecision(rule)] ??
											''}"
									>
										{ruleDecisionLabel(rule)}
									</span>
								</div>
								{#if rule.conditions && rule.conditions.length > 0}
									<div class="mb-1.5 flex flex-wrap gap-1.5">
										{#each rule.conditions as cond (cond.name)}
											<span
												class="rounded bg-[var(--surface2)] px-1.5 py-0.5 font-mono text-xs text-[var(--blue)]"
											>
												{cond.field}
												{cond.operator}
												{JSON.stringify(cond.value)}
											</span>
										{/each}
									</div>
								{/if}
								<div class="text-xs text-[var(--muted)]">{rule.reason}</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		{/each}
	{/if}
</div>
