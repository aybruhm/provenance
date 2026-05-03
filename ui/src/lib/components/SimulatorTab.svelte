<script lang="ts">
	import { session } from '$lib/stores/session';
	import { toasts } from '$lib/stores/toast';
	import { fireEvent, SCENARIOS } from '$lib/controllers/gateway';
	import type { GatewayResult } from '$lib/types/index';
	import Badge from './Badge.svelte';

	let customAction = $state('payments.initiate');
	let customDecision = $state('ALLOW');
	let customParams = $state(
		JSON.stringify({ amount: 50, currency: 'GBP', recipient_id: 'rec_abc123' }, null, 2)
	);
	let result = $state<GatewayResult | null>(null);
	let firing = $state(false);
	let activeScenario = $state<string | null>(null);

	const sessionId = `sess_${Math.random().toString(36).slice(2, 14)}`;

	async function fire(
		action: string,
		decision: string,
		params: Record<string, unknown>,
		scenario?: string
	) {
		const { agentId, tenantPolicyId } = session.data;
		if (!agentId || !tenantPolicyId) {
			toasts.add('Session not configured — complete setup first', 'err');
			return;
		}
		firing = true;
		activeScenario = scenario ?? null;
		result = null;
		try {
			result = await fireEvent(agentId, tenantPolicyId, action, decision, params, sessionId);
			const type = result.decision === 'ALLOW' ? 'ok' : result.decision === 'BLOCK' ? 'err' : 'inf';
			toasts.add(`${result.decision}: ${result.reason.slice(0, 60)}`, type);
		} catch (e) {
			toasts.add(e instanceof Error ? e.message : 'Execution failed', 'err');
		} finally {
			firing = false;
		}
	}

	async function fireScenario(key: string) {
		const s = SCENARIOS[key];
		if (!s) return;
		await fire(s.action, s.decision, s.parameters, key);
	}

	async function fireCustom() {
		let params: Record<string, unknown> = {};
		try {
			params = JSON.parse(customParams);
		} catch {
			toasts.add('Invalid JSON in parameters', 'err');
			return;
		}
		await fire(customAction, customDecision, params);
	}
</script>

<div class="flex flex-col gap-5">
	<!-- Preset scenarios -->
	<div>
		<div class="mb-2 text-xs font-semibold tracking-wider text-[var(--muted)] uppercase">
			Quick Scenarios
		</div>
		<div class="flex flex-wrap gap-2">
			{#each Object.entries(SCENARIOS) as [key, scenario]}
				<button
					onclick={() => fireScenario(key)}
					disabled={firing}
					class="rounded border px-3 py-1.5 text-xs font-medium transition-colors disabled:opacity-50 {activeScenario ===
					key
						? 'border-[var(--blue)] bg-[var(--blue-dim)] text-[var(--blue)]'
						: '`border-(--border) text-[var(--muted)] hover:border-[var(--blue)] hover:text-[var(--blue)]'}"
				>
					{scenario.label}
				</button>
			{/each}
		</div>
	</div>

	<!-- Custom event form -->
	<div class="`border-(--border) rounded border bg-[var(--surface)] p-4">
		<div class="mb-3 text-xs font-semibold tracking-wider text-[var(--muted)] uppercase">
			Custom Event
		</div>
		<div class="mb-3 grid grid-cols-2 gap-3">
			<div>
				<label for="sim-action" class="mb-1 block text-xs text-[var(--muted)]">Action</label>
				<input
					id="sim-action"
					type="text"
					bind:value={customAction}
					class="`border-(--border) w-full rounded border bg-[var(--surface2)] px-2.5 py-1.5 font-mono text-xs text-[var(--text)] focus:border-[var(--blue)] focus:outline-none"
				/>
			</div>
			<div>
				<label for="sim-decision" class="mb-1 block text-xs text-[var(--muted)]"
					>Expected Decision</label
				>
				<select
					id="sim-decision"
					bind:value={customDecision}
					class="`border-(--border) w-full rounded border bg-[var(--surface2)] px-2.5 py-1.5 text-xs text-[var(--text)] focus:border-[var(--blue)] focus:outline-none"
				>
					<option value="ALLOW">ALLOW</option>
					<option value="BLOCK">BLOCK</option>
					<option value="ESCALATE">ESCALATE</option>
				</select>
			</div>
		</div>
		<div class="mb-3">
			<label for="sim-params" class="mb-1 block text-xs text-[var(--muted)]"
				>Parameters (JSON)</label
			>
			<textarea
				id="sim-params"
				bind:value={customParams}
				rows={4}
				class="`border-(--border) w-full rounded border bg-[var(--surface2)] px-2.5 py-1.5 font-mono text-xs text-[var(--text)] focus:border-[var(--blue)] focus:outline-none"
			></textarea>
		</div>
		<button
			onclick={fireCustom}
			disabled={firing}
			class="rounded border border-[var(--blue)] bg-[var(--blue-dim)] px-4 py-2 text-xs font-semibold text-[var(--blue)] transition-opacity hover:opacity-80 disabled:opacity-50"
		>
			{firing ? 'Executing…' : 'Execute'}
		</button>
	</div>

	<!-- Result -->
	{#if result}
		<div
			class="rounded border p-4 {result.decision === 'ALLOW'
				? 'border-[var(--green)] bg-[var(--green-dim)]'
				: result.decision === 'BLOCK'
					? 'border-[var(--red)] bg-[var(--red-dim)]'
					: 'border-[var(--yellow)] bg-[var(--yellow-dim)]'}"
		>
			<div class="mb-2 flex items-center gap-3">
				<Badge decision={result.decision} />
				{#if result.escalation_id}
					<span class="text-xs text-[var(--yellow)]">Escalation created</span>
				{/if}
			</div>
			<div class="mb-2 text-xs text-[var(--text)]">{result.reason}</div>
			<div class="font-mono text-xs text-[var(--muted)]">event: {result.event_id}</div>
			{#if result.escalation_id}
				<div class="font-mono text-xs text-[var(--muted)]">esc: {result.escalation_id}</div>
			{/if}
		</div>
	{/if}
</div>
