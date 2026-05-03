<script lang="ts">
	import LoginForm from '$lib/components/LoginForm.svelte';
</script>

<div class="flex min-h-screen items-center justify-center bg-[var(--bg)] px-4">
	<div class="w-full max-w-sm">
		<!-- Logo -->
		<div class="mb-8 text-center">
			<div
				class="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-(--blue) text-lg font-bold text-white"
			>
				P
			</div>
			<h1 class="text-lg font-semibold text-[var(--text)]">Provenance</h1>
			<p class="mt-1 text-xs text-[var(--muted)]">Agentic Audit & Compliance Layer</p>
		</div>

		<!-- Card -->
		<div class="rounded-lg border `border-(--border) bg-[var(--surface)] p-6">
			<h2 class="mb-5 text-sm font-semibold text-[var(--text)]">Sign in to your account</h2>
			<LoginForm />
		</div>

		<p class="mt-4 text-center text-xs text-[var(--muted)]">
			Don't have an account?
			<a href="/signup" class="text-[var(--blue)] hover:underline">Create one</a>
		</p>
	</div>
</div>
