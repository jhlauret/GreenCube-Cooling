import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Proxies API calls to Odoo through the Vite dev server so the browser only
// ever sees one origin. This is what makes `credentials: 'include'` in
// src/api/client.ts safe without a CORS/CSRF policy in dev (audit P0-06):
// the Odoo session cookie is same-origin, so no cross-site cookie or
// preflight handling is needed. Production must reproduce this with a
// reverse proxy (nginx/traefik) in front of both services — see README.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [react(), tailwindcss()],
    server: {
      proxy: {
        '/api/v1/greencube/cooling': {
          target: env.VITE_ODOO_ORIGIN || 'http://localhost:8069',
          changeOrigin: true,
        },
      },
    },
  }
})
