import { defineConfig } from 'vitest/config';

export default defineConfig({
  ssr: { resolve: { conditions: ['source', 'node'] } },
  test: {
    globals: true,
    environment: 'node',
    pool: 'threads',
    env: { NODE_ENV: 'testing', WEBHOOK_SECRET: 'TEST_STRIPE_WEBHOOK_SECRET' },
    setupFiles: ['./test/utils/vitest-setup.ts'],
    include: [
      'test/integration/services/automations/automation-run-date-storage.test.ts',
      'test/unit/server/services/automations/database-automations-repository.test.ts',
    ],
    hookTimeout: 60000,
    testTimeout: 10000,
  },
});
