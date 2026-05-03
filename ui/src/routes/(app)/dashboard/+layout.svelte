<script lang="ts">
	import Header from '$lib/components/Header.svelte';
	import Sidebar from '$lib/components/Sidebar.svelte';
	import Toast from '$lib/components/Toast.svelte';
	import { session } from '$lib/stores/session';
	import { runIntegrity } from '$lib/controllers/integrity';

	let { children } = $props();

	let sidebarRef = $state<ReturnType<typeof Sidebar> | null>(null);
	let integrityValid = $state<boolean | null>(null);

	$effect(() => {
		const { tenantId } = session.data;
		if (!tenantId) return;

		runIntegrity(tenantId)
			.then((r) => (integrityValid = r.valid))
			.catch(() => {});
	});
</script>

<div class="flex flex-col" style="height:100dvh">
	<Header {integrityValid} />
	<div class="flex min-h-0 flex-1" style="display:grid;grid-template-columns:1fr 400px">
		<main class="overflow-y-auto p-6">
			{@render children()}
		</main>
		<Sidebar bind:this={sidebarRef} />
	</div>
</div>
<Toast />
