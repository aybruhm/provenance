import adapter from '@sveltejs/adapter-node';

/** @type {import('@sveltejs/kit').Config} */
const config = {
    compilerOptions: {
        // Force runes mode for the project, except for libraries. Can be removed in svelte 6.
        runes: ({ filename }) => (filename.split(/[/\\]/).includes('node_modules') ? undefined : true)
    },
    kit: {
        // adapter-node: `npm run build` emits a standalone server (build/index.js) for the
        // production image (docker/prod.Dockerfile).
        adapter: adapter()
    }
};

export default config;
