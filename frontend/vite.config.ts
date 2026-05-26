// C:\nxtturn\frontend\vite.config.ts

import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import basicSsl from '@vitejs/plugin-basic-ssl'

export default defineConfig(({ command, mode }) => {
  // Load environment variables if needed
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [
      vue(),
      vueDevTools(),
      // This plugin automatically turns on HTTPS for the dev server
      command === 'serve' ? basicSsl() : [],
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      host: true,
      port: 5173,
      allowedHosts: true,
      watch: {
        // Docker bind mounts can make recursive directory scans expensive.
        // Polling is a little noisier, but it is much more stable in this setup.
        usePolling: true,
        interval: 250,
        ignored: ['**/node_modules/**', '**/.git/**', '**/dist/**', '**/coverage/**', '**/.cache/**'],
      },
      // --- NEW PROXY LOGIC (The "Senior Architect" Way) ---
      proxy: {
        // Any request to /api will be sent to the Django Backend container
        '/api': {
          target: 'https://backend:8000',
          changeOrigin: true,
          // Ignore self-signed cert errors between Vite and Django
          secure: false,
        },
        // Any request to /ws will be sent to the Daphne WebSocket server
        '/ws': {
          target: 'https://backend:8000',
          changeOrigin: true,
          secure: false,
          ws: true, // Crucial for enabling WebSocket proxying
        },

        '/media': {
          target: 'https://backend:8000',
          changeOrigin: true,
          secure: false,
        },

        '/admin': {
          target: 'https://backend:8000',
          changeOrigin: true,
          secure: false,
        },
        '/static/admin': {
          target: 'https://backend:8000',
          changeOrigin: true,
          secure: false,
        },
      },
    },
  }
})
