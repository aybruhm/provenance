import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
    plugins: [tailwindcss(), sveltekit()],
    server: {
        host: "0.0.0.0",
        port: 5173,
        proxy: {
            "/api": {
                target: "http://api:8001",
                changeOrigin: true,
            },
        },
        hmr: {
            host: "localhost",
            port: 5173,
        },
        watch: {
            ignored: [
                "**/node_modules/**",
                "**/build/**",
                "**/dist/**",
                "**/.git/**",
                "**/.cache/**",
                "**/.vscode/**",
                "**/.idea/**",
                "**/logs/**",
                "**/tmp/**",
                "**/temp/**",
            ],
        },
    }
});
