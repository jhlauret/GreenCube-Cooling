import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    // e2e/**/*.spec.ts are Playwright specs (npm run test:e2e), not vitest
    // tests — without this exclusion vitest's default *.spec.ts glob picks
    // them up too and fails immediately since they use @playwright/test's
    // test()/expect(), not vitest's.
    exclude: ['**/node_modules/**', '**/e2e/**'],
  },
});
