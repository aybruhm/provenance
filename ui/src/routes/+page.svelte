<script lang="ts">
	import { goto } from '$app/navigation';
	import { session } from '$lib/stores/session';
	import { onMount } from 'svelte';

	onMount(() => {
		if (!session.isAuthenticated()) {
			goto('/login');
		} else if (!session.isSetupComplete()) {
			goto('/setup');
		} else {
			goto('/dashboard');
		}
	});
</script>
