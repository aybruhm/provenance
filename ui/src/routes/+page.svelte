<script lang="ts">
	import { goto } from '$app/navigation';
	import { session } from '$lib/stores/session';
	import { onMount } from 'svelte';

	onMount(() => {
		if (!session.isAuthenticated()) {
			goto('/login');
		} else if (!session.isSetupComplete()) {
			goto('/setup');
		} else if ((session.data.workspaces?.length ?? 0) > 0) {
			goto('/workspaces');
		} else {
			goto('/dashboard');
		}
	});
</script>
