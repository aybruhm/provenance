<script lang="ts">
	import { session } from '$lib/stores/session';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import Toast from '$lib/components/Toast.svelte';
	import { restoreAccessTokenCookie } from '../../utils/request';

	let { children } = $props();

	onMount(() => {
		if (!session.isAuthenticated()) {
			goto('/login');
			return;
		}
		restoreAccessTokenCookie();
	});
</script>

{@render children()}
<Toast />
