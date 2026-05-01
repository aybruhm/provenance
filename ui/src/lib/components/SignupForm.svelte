<script lang="ts">
	import { register } from '$lib/controllers/auth';
	import { session } from '$lib/stores/session';
	import { toasts } from '$lib/stores/toast';
	import { setAccessTokenCookie } from '../../utils/request';
	import { goto } from '$app/navigation';

	let username = $state('');
	let password = $state('');
	let confirm = $state('');
	let loading = $state(false);
	let error = $state('');

	async function handleSubmit(e: Event) {
		e.preventDefault();
		error = '';
		if (password !== confirm) {
			error = 'Passwords do not match';
			return;
		}
		loading = true;
		try {
			const user = await register(username, password);
			session.update({ userId: user.id, username: user.username, accessToken: user.accessToken });
			setAccessTokenCookie(user.accessToken);
			goto('/setup');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Registration failed';
			toasts.add(error, 'err');
		} finally {
			loading = false;
		}
	}
</script>

<form onsubmit={handleSubmit} class="flex flex-col gap-4">
	<div>
		<label for="signup-username" class="mb-1 block text-xs text-[var(--muted)]">Username</label>
		<input
			id="signup-username"
			type="text"
			bind:value={username}
			required
			autocomplete="username"
			class="`border-(--border) w-full rounded border bg-[var(--surface2)] px-3 py-2 text-sm text-[var(--text)] placeholder-[var(--muted)] focus:border-[var(--blue)] focus:outline-none"
			placeholder="choose a username"
		/>
	</div>
	<div>
		<label for="signup-password" class="mb-1 block text-xs text-[var(--muted)]">Password</label>
		<input
			id="signup-password"
			type="password"
			bind:value={password}
			required
			autocomplete="new-password"
			class="`border-(--border) w-full rounded border bg-[var(--surface2)] px-3 py-2 text-sm text-[var(--text)] placeholder-[var(--muted)] focus:border-[var(--blue)] focus:outline-none"
			placeholder="••••••••"
		/>
	</div>
	<div>
		<label for="signup-confirm" class="mb-1 block text-xs text-[var(--muted)]"
			>Confirm password</label
		>
		<input
			id="signup-confirm"
			type="password"
			bind:value={confirm}
			required
			autocomplete="new-password"
			class="`border-(--border) w-full rounded border bg-[var(--surface2)] px-3 py-2 text-sm text-[var(--text)] placeholder-[var(--muted)] focus:border-[var(--blue)] focus:outline-none"
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
		{loading ? 'Creating account…' : 'Create account'}
	</button>
</form>
