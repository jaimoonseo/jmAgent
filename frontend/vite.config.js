import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src'),
        },
    },
    server: {
        port: 6110,
        proxy: {
            '/api': {
                target: 'http://localhost:6100',
                changeOrigin: true,
                rewrite: function (path) { return path.replace(/^\/api/, '/api'); },
            },
        },
    },
    build: {
        target: 'ES2020',
        outDir: 'dist',
    },
});
