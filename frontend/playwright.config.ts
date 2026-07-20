import { defineConfig, devices } from '@playwright/test';

/**
 * E2E config for the "Parcours Playwright avec API Odoo de test" item of
 * the qualité (P2) lot. Needs a real Odoo instance with the
 * greencube_cooling module installed, reachable at VITE_ODOO_ORIGIN (same
 * env var vite.config.ts's dev proxy already uses) — there is no mocking
 * here by design, since the whole point is exercising the real API
 * contract end to end, not the component tree in isolation (that's what
 * src/**\/*.test.tsx + vitest already cover).
 *
 * `webServer` boots the Vite dev server automatically; it does NOT boot
 * Odoo — start that separately before running `npm run test:e2e`.
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  retries: 0,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'retain-on-failure',
  },
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
