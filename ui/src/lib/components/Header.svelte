<script lang="ts">
	import { session } from '$lib/stores/session';
	import { goto } from '$app/navigation';

	let { integrityValid = null }: { integrityValid?: boolean | null } = $props();

	function handleLogout() {
		session.clear();
		goto('/login');
	}
</script>

<header
	class="`border-(--border) flex items-center gap-4 border-b bg-[var(--surface)] px-5"
	style="height:60px"
>
	<!-- Logo -->
	<div class="flex items-center gap-2.5">
		<div
			class="flex h-7 w-7 items-center justify-center rounded bg-(--blue) text-sm font-bold text-white"
		>
			P
		</div>
		<div>
			<div class="text-sm font-semibold text-[var(--text)]">Provenance</div>
			<div class="text-xs text-[var(--muted)]">Agentic Audit & Compliance Layer</div>
		</div>
	</div>

	<div class="h-5 w-px bg-[var(--border)]"></div>

	<!-- Tenant chip -->
	{#if $session.tenantName}
		<div
			class="`border-(--border) flex items-center gap-1.5 rounded border px-2.5 py-1 text-xs text-[var(--muted)]"
		>
			<span class="h-1.5 w-1.5 rounded-full bg-(--blue)"></span>
			<strong class="text-[var(--text)]">{$session.tenantName}</strong>
		</div>
	{/if}

	<!-- Integrity badge -->
	{#if integrityValid !== null}
		<div
			class="flex items-center gap-1.5 rounded border px-2.5 py-1 text-xs font-semibold {integrityValid
				? 'border-[var(--green)] text-[var(--green)]'
				: 'border-[var(--red)] text-[var(--red)]'}"
		>
			{integrityValid ? '✔ Chain Valid' : '✗ Violations'}
		</div>
	{/if}

	<div class="flex-1"></div>

	<!-- LIVE indicator -->
	<div class="flex items-center gap-1.5 text-xs text-[var(--muted)]">
		<span class="relative flex h-2 w-2">
			<span
				class="absolute inline-flex h-full w-full animate-ping rounded-full bg-(--green) opacity-75"
			></span>
			<span class="relative inline-flex h-2 w-2 rounded-full bg-(--green)"></span>
		</span>
		LIVE
	</div>

	<!-- User + logout -->
	{#if $session.username}
		<div class="flex items-center gap-3">
			<span class="text-xs text-[var(--muted)]">{$session.username}</span>
			<button
				onclick={handleLogout}
				class="`border-(--border) rounded border px-2.5 py-1 text-xs text-[var(--muted)] transition-colors hover:border-[var(--red)] hover:text-[var(--red)]"
			>
				Sign out
			</button>
		</div>
	{/if}
</header>
